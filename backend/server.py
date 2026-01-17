import uvicorn
from fastapi import FastAPI
from search import search_news
from scrapers.cnn import fetch_cnn
from scrapers.fox import fetch_fox

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "goon"}


@app.get("/search")
async def search(q: str):
    results = search_news(q, "cnn.com, foxnews.com")["articles"]

    outputs = []
    cnn_count = 0
    fox_count = 0

    for article in results:
        if len(outputs) >= 200:
            break

        if "cnn.com" in article["url"]:
            if cnn_count >= 10:
                continue
            content = fetch_cnn(article["url"])
            source = "CNN"
            cnn_count += 1
        elif "foxnews.com" in article["url"]:
            if fox_count >= 10:
                continue
            content = fetch_fox(article["url"])
            source = "Fox"
            fox_count += 1
        else:
            continue

        output = {
            "source": source,
            "title": article["title"],
            "url": article["url"],
            "content": content,
            "comments": [],
        }
        outputs.append(output)

    return outputs


if __name__ == "__main__":
    uvicorn.run("server:app")
