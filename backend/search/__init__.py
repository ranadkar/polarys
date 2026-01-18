"""Search modules for different platforms."""
from search.news import search_news
from search.reddit import search_reddit
from search.bluesky import search_bluesky

__all__ = ["search_news", "search_reddit", "search_bluesky"]
