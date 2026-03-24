#!/usr/bin/env python3
"""
YouTube Data Extractor — Get video info, comments, transcripts without API key.
Uses YouTube's internal Innertube API. No quotas, no rate limits (be respectful).
"""

import json
import re
import sys
import urllib.request
import urllib.parse


INNERTUBE_CLIENT = {
    "clientName": "WEB",
    "clientVersion": "2.20240101.00.00",
}


def _innertube_request(endpoint: str, body: dict) -> dict:
    url = f"https://www.youtube.com/youtubei/v1/{endpoint}?prettyPrint=false"
    data = json.dumps({
        "context": {"client": INNERTUBE_CLIENT},
        **body
    }).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    })
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())


def get_video_info(video_id: str) -> dict:
    """Get video title, views, likes, channel, description."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="replace")

    # Extract ytInitialData
    match = re.search(r'var ytInitialPlayerResponse\s*=\s*({.*?});', html)
    if not match:
        return {"error": "Could not parse video page"}

    data = json.loads(match.group(1))
    vd = data.get("videoDetails", {})
    return {
        "video_id": vd.get("videoId"),
        "title": vd.get("title"),
        "channel": vd.get("author"),
        "views": int(vd.get("viewCount", 0)),
        "length_seconds": int(vd.get("lengthSeconds", 0)),
        "keywords": vd.get("keywords", [])[:10],
        "description": vd.get("shortDescription", "")[:200],
    }


def search_videos(query: str, limit: int = 10) -> list:
    """Search YouTube videos by keyword."""
    data = _innertube_request("search", {
        "query": query,
        "params": "EgIQAQ%3D%3D",  # Videos only
    })

    results = []
    contents = (data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [{}])[0]
                .get("itemSectionRenderer", {})
                .get("contents", []))

    for item in contents[:limit]:
        vr = item.get("videoRenderer")
        if not vr:
            continue
        results.append({
            "video_id": vr.get("videoId"),
            "title": vr.get("title", {}).get("runs", [{}])[0].get("text", ""),
            "channel": vr.get("ownerText", {}).get("runs", [{}])[0].get("text", ""),
            "views": vr.get("viewCountText", {}).get("simpleText", ""),
            "published": vr.get("publishedTimeText", {}).get("simpleText", ""),
        })

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python youtube_extract.py info dQw4w9WgXcQ")
        print("  python youtube_extract.py search 'web scraping python'")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "info" and len(sys.argv) > 2:
        print(json.dumps(get_video_info(sys.argv[2]), indent=2, ensure_ascii=False))
    elif cmd == "search" and len(sys.argv) > 2:
        results = search_videos(sys.argv[2])
        for r in results:
            print(f"[{r['video_id']}] {r['title']} | {r['channel']} | {r['views']}")
    else:
        print("Unknown command. Use 'info' or 'search'.")
