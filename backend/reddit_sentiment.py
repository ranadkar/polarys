import os
from dotenv import load_dotenv
import asyncpraw
import asyncio
import time
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()
app_id = os.getenv("REDDIT_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET")
reddit_user_agent = os.getenv("REDDIT_USER_AGENT")
analyzer = SentimentIntensityAnalyzer()


async def search_reddit(reddit, query: str, subreddit_name: str = "all", limit: int = 50):
    if not query:
        return None
    
    posts = []
    
    subreddit = await reddit.subreddit(subreddit_name)
    async for submission in subreddit.search(query, limit=limit, sort="relevance"):
        text_content = submission.title + " " + (submission.selftext or "")
        sentiment_scores = analyzer.polarity_scores(text_content)
        compound_score = sentiment_scores["compound"]

        sentiment_category = (
            "positive" if compound_score >= 0.05 
            else "negative" if compound_score <= -0.05 
            else "neutral"
        )

        posts.append({
            "source": "Reddit",
            "id": submission.id,
            "title": submission.title,
            "username": f"u/{submission.author.name}" if submission.author else "u/[deleted]",
            "handle": submission.author.name if submission.author else "[deleted]",
            "contents": submission.selftext[:500] if submission.selftext else "[Link post]",
            "platform": "reddit",
            "date": submission.created_utc,
            "created_utc": submission.created_utc,
            "sentiment": sentiment_category,
            "sentiment_score": compound_score,
            "score": submission.score,
            "likes": submission.score,
            "num_comments": submission.num_comments,
            "url": f"https://reddit.com{submission.permalink}",
            "subreddit": submission.subreddit.display_name if submission.subreddit else "unknown",
        })

    if not posts:
        return None

    # Calculate overall sentiment
    avg_score = sum(p["sentiment_score"] for p in posts) / len(posts)
    overall_sentiment = (
        "Positive sentiment" if avg_score >= 0.05 
        else "Negative sentiment" if avg_score <= -0.05 
        else "Neutral sentiment"
    )

    # Save results
    output_file = f"sentiment_analysis_{subreddit_name}_{query.replace(' ', '_')}_{len(posts)}.json"
    result = {
        "query": query,
        "subreddit": subreddit_name,
        "overall_sentiment": overall_sentiment,
        "average_score": avg_score,
        "post_count": len(posts),
        "posts": posts,
        "timestamp": time.time(),
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Analysis complete. Saved to: {output_file}")
    return result


if __name__ == "__main__":
    import sys
    
    async def main():
        query = sys.argv[1] if len(sys.argv) > 1 else input("Enter your search query: ").strip()
        subreddit_name = sys.argv[2] if len(sys.argv) > 2 else (input("Enter subreddit to search (default: all): ").strip() or "all")
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else (int(input("How many posts to retrieve? (default: 50): ").strip() or "50"))
        
        reddit = asyncpraw.Reddit(
            client_id=app_id,
            client_secret=client_secret,
            user_agent=reddit_user_agent,
        )
        
        try:
            await search_reddit(reddit, query, subreddit_name, limit)
        finally:
            await reddit.close()
    
    asyncio.run(main())