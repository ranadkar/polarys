import os
from dotenv import load_dotenv
import asyncpraw
import random
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()
app_id = os.getenv("REDDIT_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET")

analyzer = SentimentIntensityAnalyzer()


def get_async_reddit():
    return asyncpraw.Reddit(
        client_id=app_id,
        client_secret=client_secret,
        user_agent="android:" + app_id + ":v1.0 (by u/K6av6ai82j0zo8HB721)"
    )


async def test_scrape():
    import asyncio
    
    reddit = get_async_reddit()
    
    # Test by fetching hot posts from r/conservative
    subreddit = await reddit.subreddit("conservative")
    print(f"Testing Reddit scraping from r/conservative...\n")
    
    count = 0
    try:
        async for submission in subreddit.hot(limit=5):
            count += 1
            print(f"Post {count}:")
            print(f"  Title: {submission.title}")
            print(f"  Score: {submission.score}")
            print(f"  Comments: {submission.num_comments}")
            
            # Analyze sentiment
            sentiment = analyzer.polarity_scores(submission.title)
            print(f"  Sentiment: {sentiment}")
            print()
            
            # Add delay to avoid rate limiting (Reddit recommends max 60 requests per minute)
            await asyncio.sleep(0.2)
    
    except Exception as e:
        print(f"Error occurred: {e}")
        if "429" in str(e) or "rate" in str(e).lower():
            print("Rate limit hit! Waiting before retry...")
            await asyncio.sleep(60)
    
    finally:
        await reddit.close()
        print(f"Successfully scraped {count} posts!")


async def scrape_subreddit_posts():
    import asyncio
    import json
    import time
    from datetime import datetime
    
    reddit = get_async_reddit()
    
    try:
        # Target: r/PoliticalDebate, scrape 1000 posts with all comments
        subreddit_name = "PoliticalDebate"
        target_posts = 1000
        
        subreddit = await reddit.subreddit(subreddit_name)
        print(f"Starting to scrape {target_posts} posts from r/{subreddit_name}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        all_posts = []
        post_count = 0
        request_count = 0
        start_time = time.time()
        
        # Build the Comment structure recursively
        async def build_comment_dict(comment, depth=0):
            # Skip MoreComments objects
            if isinstance(comment, asyncpraw.models.MoreComments):
                return None
            
            # Skip AutoModerator comments
            if str(comment.author).lower() == "automoderator":
                return None
            
            comment_data = {
                "url": f"https://reddit.com{comment.permalink}",
                "content": comment.body,
                "author": str(comment.author),
                "score": comment.score,
                "replies": [],
                "depth": depth
            }
            
            # Get all replies (limit depth to 3 to avoid infinite nesting)
            if depth < 3 and hasattr(comment, 'replies') and comment.replies:
                for reply in comment.replies:
                    if not isinstance(reply, asyncpraw.models.MoreComments):
                        reply_data = await build_comment_dict(reply, depth + 1)
                        if reply_data:
                            comment_data["replies"].append(reply_data)
            
            return comment_data
        
        # Scrape posts from hot, then top if needed
        async for submission in subreddit.hot(limit=target_posts):
            if post_count >= target_posts:
                break
            
            try:
                # Load submission to access comments
                await submission.load()
                request_count += 1
                
                # Fetch all top-level comments (asyncpraw handles rate limiting internally)
                comments_list = []
                async for comment in submission.comments:
                    if not isinstance(comment, asyncpraw.models.MoreComments):
                        comment_data = await build_comment_dict(comment, depth=0)
                        if comment_data:
                            comments_list.append(comment_data)
                
                # Build the Post structure
                post_data = {
                    "source": "Reddit",
                    "title": submission.title,
                    "ai_summary": f"Post about {submission.title[:50]}... with {submission.num_comments} comments and {submission.score} upvotes",
                    "contents": submission.selftext if submission.selftext else "[Link post - no text content]",
                    "url": f"https://reddit.com{submission.permalink}",
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "comments": comments_list
                }
                
                all_posts.append(post_data)
                post_count += 1
                
                # Progress update every 10 posts
                if post_count % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"Progress: {post_count}/{target_posts} posts scraped | "
                          f"Elapsed: {elapsed/60:.1f} min | "
                          f"Last: {submission.title[:60]}...")
                    
                    # Save checkpoint every 50 posts
                    if post_count % 50 == 0:
                        checkpoint_file = f"checkpoint_{post_count}.json"
                        with open(checkpoint_file, 'w', encoding='utf-8') as f:
                            json.dump(all_posts, f, indent=2, ensure_ascii=False)
                        print(f"  → Checkpoint saved: {checkpoint_file}")
                
            except Exception as e:
                print(f"Error processing post {post_count + 1}: {e}")
                continue
        
        # Save final results
        output_file = f"r_{subreddit_name}_{post_count}_posts.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, indent=2, ensure_ascii=False)
        
        elapsed = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"Scraping complete!")
        print(f"Total posts scraped: {post_count}")
        print(f"Total time: {elapsed/60:.1f} minutes ({elapsed/3600:.1f} hours)")
        print(f"Output file: {output_file}")
        print(f"{'='*80}")
    
    except Exception as e:
        print(f"Fatal error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await reddit.close()
        print("Done!")


if __name__ == "__main__":
    import asyncio
    # asyncio.run(test_scrape())
    asyncio.run(scrape_subreddit_posts())