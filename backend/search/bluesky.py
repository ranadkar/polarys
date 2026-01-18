import os
from dotenv import load_dotenv
import asyncio
from atproto import AsyncClient
from datetime import datetime

load_dotenv()
bluesky_handle = os.getenv("BLUESKY_HANDLE")
bluesky_password = os.getenv("BLUESKY_APP_PASSWORD")


def to_epoch_time(iso_timestamp: str) -> int:
    """Convert ISO 8601 UTC timestamp to epoch time."""
    if not iso_timestamp:
        return 0
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return 0


async def search_bluesky(client, query: str, sort: str = "top", limit: int = 50):
    if not query:
        return None

    if sort not in ["latest", "top"]:
        sort = "top"

    limit = min(limit, 100)
    posts = []

    # Search for posts
    response = await client.app.bsky.feed.search_posts(
        {"q": query, "limit": limit, "sort": sort}
    )

    for post in response.posts[:limit]:
        text_content = post.record.text if hasattr(post.record, "text") else ""

        # Skip posts with no text content (video-only posts) or content less than 100 characters
        if (
            not text_content
            or not text_content.strip()
            or len(text_content.strip()) < 100
        ):
            continue

        author_handle = (
            post.author.handle if hasattr(post.author, "handle") else "unknown"
        )
        author_display = (
            post.author.display_name
            if hasattr(post.author, "display_name")
            else author_handle
        )

        post_uri_parts = post.uri.split("/")
        post_id = post_uri_parts[-1] if len(post_uri_parts) > 0 else ""
        post_url = f"https://bsky.app/profile/{author_handle}/post/{post_id}"

        posts.append(
            {
                "source": "Bluesky",
                "id": post_id,
                "title": text_content[:100] + "..."
                if len(text_content) > 100
                else text_content,
                "author": f"@{author_handle}",
                "display_name": author_display,
                "contents": text_content,
                "date": to_epoch_time(post.record.created_at),
                "score": post.like_count,
                "reposts": post.repost_count,
                "replies": post.reply_count,
                "quotes": post.quote_count,
                "bookmarks": post.bookmark_count,
                "url": post_url,
            }
        )

    return posts


if __name__ == "__main__":
    import sys

    async def main():
        query = (
            sys.argv[1]
            if len(sys.argv) > 1
            else input("Enter your search query: ").strip()
        )
        sort = (
            sys.argv[2]
            if len(sys.argv) > 2
            else (input("Sort by (latest/top, default: top): ").strip() or "top")
        )
        limit = (
            int(sys.argv[3])
            if len(sys.argv) > 3
            else (
                int(
                    input(
                        "How many posts to retrieve? (default: 50, max: 100): "
                    ).strip()
                    or "50"
                )
            )
        )

        client = AsyncClient()
        await client.login(bluesky_handle, bluesky_password)

        try:
            await search_bluesky(client, query, sort, limit)
        finally:
            pass

    asyncio.run(main())
