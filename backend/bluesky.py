import os
from dotenv import load_dotenv
import asyncio
import time
import json
from atproto import AsyncClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()
bluesky_handle = os.getenv("BLUESKY_HANDLE")
bluesky_password = os.getenv("BLUESKY_APP_PASSWORD")

analyzer = SentimentIntensityAnalyzer()


def get_async_client():
    """Create and return an async Bluesky client."""
    return AsyncClient()


async def get_bluesky_search_data(query: str, limit: int = 50, sort: str = "latest"):
    """Fetch Bluesky posts with sentiment analysis for any search query."""
    client = get_async_client()
    posts = []

    try:
        # Login to Bluesky
        await client.login(bluesky_handle, bluesky_password)

        # Search for posts
        response = await client.app.bsky.feed.search_posts(
            {"q": query, "limit": min(limit, 100), "sort": sort}
        )

        for post in response.posts[:limit]:
            # Extract text content
            text_content = post.record.text if hasattr(post.record, "text") else ""

            # Perform sentiment analysis
            sentiment_scores = analyzer.polarity_scores(text_content)
            compound_score = sentiment_scores["compound"]

            if compound_score >= 0.05:
                sentiment_category = "positive"
            elif compound_score <= -0.05:
                sentiment_category = "negative"
            else:
                sentiment_category = "neutral"

            # Extract author information
            author_handle = post.author.handle if hasattr(post.author, "handle") else "unknown"
            author_display = (
                post.author.display_name
                if hasattr(post.author, "display_name")
                else author_handle
            )

            # Build post URL
            post_uri_parts = post.uri.split("/")
            post_id = post_uri_parts[-1] if len(post_uri_parts) > 0 else ""
            post_url = f"https://bsky.app/profile/{author_handle}/post/{post_id}"

            posts.append(
                {
                    "source": "Bluesky",
                    "id": post_id,
                    "uri": post.uri,
                    "title": text_content[:100] + "..." if len(text_content) > 100 else text_content,
                    "username": f"@{author_handle}",
                    "handle": author_handle,
                    "display_name": author_display,
                    "contents": text_content,
                    "platform": "bluesky",
                    "date": post.record.created_at if hasattr(post.record, "created_at") else "",
                    "created_at": post.record.created_at if hasattr(post.record, "created_at") else "",
                    "sentiment": sentiment_category,
                    "sentiment_score": compound_score,
                    "likes": post.like_count,
                    "reposts": post.repost_count,
                    "replies": post.reply_count,
                    "quotes": post.quote_count if hasattr(post, "quote_count") else 0,
                    "bookmarks": post.bookmark_count if hasattr(post, "bookmark_count") else 0,
                    "url": post_url,
                    "ai_summary": f"{sentiment_category.title()} sentiment post: {text_content[:50]}...",
                }
            )
    except Exception as e:
        print(f"Error fetching Bluesky data: {e}")
        import traceback
        traceback.print_exc()

    return posts


async def categorize_overall_sentiment(query: str, limit: int = 50, sort: str = "latest"):
    """Get overall sentiment analysis for a search query on Bluesky."""
    posts = await get_bluesky_search_data(query, limit, sort)

    if not posts:
        return {
            "sentiment": "No sentiment data available",
            "score": 0.0,
            "post_count": 0,
            "posts": [],
        }

    sentiment_scores = [post["sentiment_score"] for post in posts]
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

    if avg_sentiment >= 0.05:
        category = "Positive sentiment"
    elif avg_sentiment <= -0.05:
        category = "Negative sentiment"
    else:
        category = "Neutral sentiment"

    return {
        "sentiment": category,
        "score": avg_sentiment,
        "post_count": len(posts),
        "posts": posts,
    }


async def search_posts_fast():
    """Fast sentiment-analyzed Bluesky search with instant results."""
    try:
        query = input("Enter your search query: ").strip()
        if not query:
            print("No query provided. Exiting.")
            return

        sort = input("Sort by (latest/top, default: latest): ").strip() or "latest"
        if sort not in ["latest", "top"]:
            print(f"Invalid sort option '{sort}', using 'latest'")
            sort = "latest"

        limit = input("How many posts to retrieve? (default: 50, max: 100): ").strip()
        limit = int(limit) if limit.isdigit() else 50
        limit = min(limit, 100)

        print(f"\nSearching Bluesky for: '{query}' (up to {limit} posts, sorted by {sort})...")
        print("Analyzing sentiment...")

        start_time = time.time()

        # Get posts with sentiment analysis
        result = await categorize_overall_sentiment(query, limit, sort)
        posts = result["posts"]

        elapsed = time.time() - start_time

        if not posts:
            print("No results found.")
            return

        # Save results
        output_file = f"sentiment_analysis_bluesky_{query.replace(' ', '_')}_{len(posts)}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "query": query,
                    "platform": "bluesky",
                    "sort": sort,
                    "overall_sentiment": result["sentiment"],
                    "average_score": result["score"],
                    "post_count": result["post_count"],
                    "posts": posts,
                    "timestamp": time.time(),
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"Analysis complete. Saved to: {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(search_posts_fast())
