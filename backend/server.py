import asyncio
import os
import re
import uuid
import uvicorn
from datetime import datetime

import asyncpraw
from dotenv import load_dotenv
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from reddit_sentiment import search_reddit
from bluesky import search_bluesky
from scrapers.cnn import fetch_cnn
from scrapers.fox import fetch_fox
from scrapers.cbs import fetch_cbs
from scrapers.nbc import fetch_nbc
from scrapers.abc import fetch_abc
from scrapers.breitbart import fetch_breitbart
from scrapers.nypost import fetch_nypost
from scrapers.oann import fetch_oann
from search_news import search_news
from atproto import AsyncClient

load_dotenv()


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return text
    # Remove HTML tags
    clean_text = re.sub(r"<[^>]+>", "", text)
    # Normalize all whitespace (spaces, newlines, tabs, etc.) to single spaces
    clean_text = re.sub(r"\s+", " ", clean_text)
    # Clean up extra whitespace at start/end
    clean_text = clean_text.strip()
    return clean_text


def to_epoch_time(iso_timestamp: str) -> int:
    """Convert ISO 8601 UTC timestamp to epoch time."""
    if not iso_timestamp:
        return 0
    # Parse ISO 8601 format like "2026-01-16T22:36:55Z"
    dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    return int(dt.timestamp())


client = OpenAI()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

reddit = asyncpraw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

bluesky_client = AsyncClient()
bluesky_logged_in = False

sentiment_analyzer = SentimentIntensityAnalyzer()

# Global storage for sessions keyed by session_id
# Each session contains articles_by_url dict
sessions = {}

# Global cache for scraped full content
scraped_content_cache = {}

# Outlet configuration mapping
OUTLETS = {
    "cnn.com": {"source": "CNN", "bias": "left", "scraper": fetch_cnn},
    "cbsnews.com": {"source": "CBS News", "bias": "left", "scraper": fetch_cbs},
    "nbcnews.com": {"source": "NBC News", "bias": "left", "scraper": fetch_nbc},
    "abcnews.go.com": {"source": "ABC News", "bias": "left", "scraper": fetch_abc},
    "foxnews.com": {"source": "Fox News", "bias": "right", "scraper": fetch_fox},
    "breitbart.com": {
        "source": "Breitbart",
        "bias": "right",
        "scraper": fetch_breitbart,
    },
    "nypost.com": {"source": "NY Post", "bias": "right", "scraper": fetch_nypost},
    "oann.com": {"source": "OANN", "bias": "right", "scraper": fetch_oann},
}


def analyze_sentiment(title: str, content: str) -> tuple[str, float]:
    """Analyze sentiment of text and return category and score."""
    text_content = title + " " + (content or "")
    sentiment_scores = sentiment_analyzer.polarity_scores(text_content)
    compound_score = sentiment_scores["compound"]

    sentiment_category = (
        "positive"
        if compound_score >= 0.05
        else "negative"
        if compound_score <= -0.05
        else "neutral"
    )

    return sentiment_category, compound_score


async def classify_bias(title: str, content: str, subreddit: str = "") -> str:
    """Use OpenAI to classify political bias of a post as 'left' or 'right'."""
    try:
        subreddit_info = f"\nSubreddit: r/{subreddit}" if subreddit else ""
        prompt = f"""Analyze the political bias of this social media post. Classify it as either 'left' (liberal/progressive) or 'right' (conservative).

Title: {title}
Content: {content[:500]}{subreddit_info}

Respond with ONLY one word: either 'left' or 'right'."""

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        bias = response.choices[0].message.content.strip().lower()
        return bias if bias in ["left", "right"] else "left"
    except Exception as e:
        print(f"Error classifying bias: {e}")
        return "left"


@app.get("/")
async def root():
    return {"message": "Welcome to the News Sentiment and Bias Analysis API"}


@app.get("/search")
async def search(q: str):
    global bluesky_logged_in

    # Generate a new session ID for this search
    session_id = str(uuid.uuid4())
    sessions[session_id] = {}

    # Login to Bluesky if not already logged in
    if not bluesky_logged_in:
        await bluesky_client.login(
            os.getenv("BLUESKY_HANDLE"), os.getenv("BLUESKY_APP_PASSWORD")
        )
        bluesky_logged_in = True

    # Run news search, Reddit search, and Bluesky search in parallel
    news_task = asyncio.create_task(
        asyncio.to_thread(
            search_news,
            q,
            "cnn.com, cbsnews.com, nbcnews.com, abcnews.go.com, foxnews.com, breitbart.com, nypost.com, oann.com",
        )
    )
    reddit_task = asyncio.create_task(search_reddit(reddit, q, "all", limit=20))
    bluesky_task = asyncio.create_task(
        search_bluesky(bluesky_client, q, "top", limit=20)
    )

    # Wait for all to complete
    news_results, reddit_posts, bluesky_result = await asyncio.gather(
        news_task, reddit_task, bluesky_task
    )

    results = news_results["articles"]
    outputs = []
    left_count = 0
    right_count = 0

    for article in results:
        if len(outputs) >= 50:
            break

        # Find matching outlet
        outlet_info = next(
            (info for domain, info in OUTLETS.items() if domain in article["url"]), None
        )
        if not outlet_info:
            continue

        # Filter out articles with less than 100 characters of content
        clean_content = strip_html_tags(article["content"])
        if len(clean_content) < 100:
            continue

        bias = outlet_info["bias"]
        source = outlet_info["source"]

        # Check if we've hit the limit for this bias type
        if bias == "left":
            if left_count >= 20:
                continue
            left_count += 1
        else:  # right
            if right_count >= 20:
                continue
            right_count += 1

        sentiment, sentiment_score = analyze_sentiment(article["title"], clean_content)

        output = {
            "source": source,
            "title": article["title"],
            "url": article["url"],
            "contents": clean_content,
            "bias": bias,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "author": article["author"],
            "date": to_epoch_time(article["publishedAt"]),
        }
        outputs.append(output)
        sessions[session_id][article["url"]] = output

    # Analyze sentiment and classify bias for Reddit posts
    bias_tasks = [
        classify_bias(
            post["title"], post.get("contents", ""), post.get("subreddit", "")
        )
        for post in reddit_posts
    ]
    biases = await asyncio.gather(*bias_tasks)

    # Add bias and sentiment to each Reddit post
    for post, bias in zip(reddit_posts, biases):
        post["bias"] = bias
        sentiment, sentiment_score = analyze_sentiment(
            post["title"], post.get("contents", "")
        )
        post["sentiment"] = sentiment
        post["sentiment_score"] = sentiment_score
        outputs.append(post)
        sessions[session_id][post["url"]] = post

    # Process Bluesky posts (now returns list directly like Reddit)
    bluesky_posts = bluesky_result if bluesky_result else []

    # Analyze sentiment and classify bias for Bluesky posts
    bluesky_bias_tasks = [
        classify_bias(post["title"], post.get("contents", ""), "")
        for post in bluesky_posts
    ]
    bluesky_biases = await asyncio.gather(*bluesky_bias_tasks)

    # Add bias and sentiment to each Bluesky post
    for post, bias in zip(bluesky_posts, bluesky_biases):
        post["bias"] = bias
        sentiment, sentiment_score = analyze_sentiment(
            post["title"], post.get("contents", "")
        )
        post["sentiment"] = sentiment
        post["sentiment_score"] = sentiment_score
        outputs.append(post)
        sessions[session_id][post["url"]] = post

    return {"session_id": session_id, "results": outputs}


@app.get("/summary")
async def summary(url: str, session_id: str):
    """Generate a summary for a given article URL."""
    # Check if the session exists
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please search for content first.")

    articles_by_url = sessions[session_id]

    # Check if the URL exists in our session
    if url not in articles_by_url:
        raise HTTPException(status_code=404, detail="URL not found in this session. Please search for content first.")

    article = articles_by_url[url]
    source = article.get("source", "")

    # Determine if this is a news article that needs scraping
    if source in [
        "CNN",
        "CBS News",
        "NBC News",
        "ABC News",
        "Fox News",
        "Breitbart",
        "NY Post",
        "OANN",
    ]:
        # Check cache first
        if url in scraped_content_cache:
            content_to_summarize = scraped_content_cache[url]
        else:
            # Find the appropriate scraper
            scraper = None
            for domain, info in OUTLETS.items():
                if domain in url:
                    scraper = info.get("scraper")
                    break

            if scraper:
                try:
                    # Scrape the full content
                    full_content = await asyncio.to_thread(scraper, url)
                    scraped_content_cache[url] = full_content
                    content_to_summarize = full_content
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    # Fallback to existing content
                    content_to_summarize = article.get("contents", "")
            else:
                content_to_summarize = article.get("contents", "")
    else:
        # Reddit or Bluesky - use existing content
        content_to_summarize = article.get("contents", "")

    # Generate summary using OpenAI
    try:
        title = article.get("title", "")
        prompt = f"""Provide a concise summary (3-5 sentences) of the following article. The summary MUST be in English, regardless of the original language.

Title: {title}

Content:
{content_to_summarize[:3000]}

Summary (in English):"""

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        summary_text = response.choices[0].message.content.strip()

        return {"url": url, "title": title, "source": source, "summary": summary_text}
    except Exception as e:
        print(f"Error generating summary: {e}")
        return {"error": f"Failed to generate summary: {str(e)}"}


@app.post("/insights")
async def insights(session_id: str = Body(...), articles: list[dict] = Body(...)):
    """
    Generate key takeaways for left and right perspectives, plus common ground.

    Args:
        session_id: The session ID from the search endpoint
        articles: List of dicts with 'url' and 'bias' keys

    Returns:
        {
            "key_takeaway_left": str,
            "key_takeaway_right": str,
            "common_ground": str
        }
    """
    # Check if the session exists
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please search for content first.")

    articles_by_url = sessions[session_id]

    # Separate articles by bias
    left_articles = []
    right_articles = []

    for item in articles:
        url = item.get("url")
        bias = item.get("bias")

        if url not in articles_by_url:
            continue

        article = articles_by_url[url]

        # Get full content if it's a news article
        source = article.get("source", "")
        if source in [
            "CNN",
            "CBS News",
            "NBC News",
            "ABC News",
            "Fox News",
            "Breitbart",
            "NY Post",
            "OANN",
        ]:
            # Check cache first
            if url in scraped_content_cache:
                content = scraped_content_cache[url]
            else:
                scraper = None
                for domain, info in OUTLETS.items():
                    if domain in url:
                        scraper = info.get("scraper")
                        break

                if scraper:
                    try:
                        full_content = await asyncio.to_thread(scraper, url)
                        scraped_content_cache[url] = full_content
                        content = full_content
                    except Exception as e:
                        print(f"Error scraping {url}: {e}")
                        content = article.get("contents", "")
                else:
                    content = article.get("contents", "")
        else:
            content = article.get("contents", "")

        article_data = {
            "title": article.get("title", ""),
            "source": source,
            "content": content[:2000],  # Limit content length
        }

        if bias == "left":
            left_articles.append(article_data)
        elif bias == "right":
            right_articles.append(article_data)

    # Build context strings
    left_context = "\n\n".join(
        [f"[{a['source']}] {a['title']}\n{a['content']}" for a in left_articles]
    )

    right_context = "\n\n".join(
        [f"[{a['source']}] {a['title']}\n{a['content']}" for a in right_articles]
    )

    # Generate insights using OpenAI
    try:
        prompt = f"""Analyze the following articles from different political perspectives and provide insights.

LEFT-LEANING ARTICLES:
{left_context[:8000]}

RIGHT-LEANING ARTICLES:
{right_context[:8000]}

Provide three things:
1. key_takeaway_left: A 2-3 sentence key insight or takeaway from the left-leaning perspective
2. key_takeaway_right: A 2-3 sentence key insight or takeaway from the right-leaning perspective
3. common_ground: An array of EXACTLY 3 objects, each with:
   - "title": A short 2-4 word title for the common ground area (e.g., "Infrastructure Modernization", "Data Privacy Rights", "Energy Security")
   - "bullet_point": A complete sentence describing the common ground or shared concern in that area

Format your response as JSON with these three keys: key_takeaway_left (string), key_takeaway_right (string), common_ground (array of 3 objects with title and bullet_point)"""

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        insights_text = response.choices[0].message.content.strip()

        # Parse the JSON response
        import json

        insights_data = json.loads(insights_text)

        return {
            "key_takeaway_left": insights_data.get("key_takeaway_left", ""),
            "key_takeaway_right": insights_data.get("key_takeaway_right", ""),
            "common_ground": insights_data.get("common_ground", ""),
        }
    except Exception as e:
        print(f"Error generating insights: {e}")
        return {"error": f"Failed to generate insights: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run("server:app")
