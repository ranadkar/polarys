"""Sentiment analysis and bias classification."""
import asyncio
from openai import OpenAI
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize analyzers
client = OpenAI()
sentiment_analyzer = SentimentIntensityAnalyzer()


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


async def generate_summary(title: str, content: str) -> str:
    """Generate a concise summary of article content."""
    try:
        prompt = f"""Provide a concise summary (3-5 sentences) of the following article. The summary MUST be in English, regardless of the original language.

Title: {title}

Content:
{content[:3000]}

Summary (in English):"""

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        raise


async def generate_insights(left_context: str, right_context: str) -> dict:
    """Generate key takeaways and common ground from articles."""
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

        import json
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"Error generating insights: {e}")
        raise
