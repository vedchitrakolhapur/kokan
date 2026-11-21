import json
import requests
import yt_dlp
from bs4 import BeautifulSoup
from datetime import datetime

HOME_URL = "https://kokansadlive.com/kokan.html"
KOKAN_ALL_URL = "https://kokansadlive.com/c/kokan"
YOUTUBE_VIDEOS_URL = "https://www.youtube.com/@KokansadLiveNews/videos"

ALLOWED_CATEGORIES = [
    "लक्ष्यवेधी", "देश-विदेश", "महाराष्ट्र",
    "क्राईम", "मनोरंजन", "क्रीडा", "आरोग्य"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def scrape_kokan_all():
    """https://kokansadlive.com/c/kokan वरून सर्व ३० बातम्या काढते"""
    items = []
    try:
        res = requests.get(KOKAN_ALL_URL, headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        cards = soup.select(".sub-categry-section .left-container .breaking-news-content")
        for card in cards:
            title_tag = card.select_one(".upper-text span")
            link_tag = card.select_one(".lower-text a")
            img_tag = card.select_one(".img img")
            date_tag = card.select_one(".date-text span")

            if title_tag and link_tag and link_tag.get("href"):
                items.append({
                    "title": title_tag.get_text(strip=True),
                    "link": link_tag["href"],
                    "image": img_tag["src"] if img_tag and img_tag.get("src") else "",
                    "date": date_tag.get_text(strip=True) if date_tag else "कोकण"
                })
    except Exception as e:
        print("Error scraping /c/kokan:", e)

    return items

def scrape_youtube():
    """yt-dlp वापरून @KokansadLiveNews चे अगदी ताजे १५ व्हिडिओ काढते"""
    videos = []
    try:
        ydl_opts = {
            "extract_flat": True,
            "playlistend": 15,
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(YOUTUBE_VIDEOS_URL, download=False)
            for entry in info.get("entries", []):
                vid_id = entry.get("id")
                title = entry.get("title")
                duration = entry.get("duration_string") or "YouTube Video"
                if vid_id and title:
                    videos.append({
                        "title": title.strip(),
                        "link": f"https://www.youtube.com/watch?v={vid_id}",
                        "image": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                        "date": duration
                    })
    except Exception as e:
        print("Error scraping YouTube:", e)

    return videos

def scrape_news():
    response = requests.get(HOME_URL, headers=HEADERS, timeout=15)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    data = {
        "updated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "categories": [],
        "youtube": scrape_youtube()
    }

    # १. मुख्य सेक्शन: ठळक बातम्या
    data["categories"].append({
        "name": "ठळक बातम्या",
        "items": scrape_kokan_all()
    })

    # २. इतर कॅटेगरी
    for section in soup.find_all("section", class_="blogs"):
        cat_heading = section.select_one(".breaking-news h6")
        if not cat_heading:
            continue
        cat_name = cat_heading.get_text(strip=True)

        if cat_name not in ALLOWED_CATEGORIES:
            continue

        items = []
        for slide in section.select(".swiper-slide.slide"):
            a_tag = slide.select_one(".content a.title")
            img_tag = slide.select_one(".image img")
            date_tag = slide.select_one(".content p")

            if a_tag:
                items.append({
                    "title": a_tag.get_text(strip=True),
                    "link": a_tag["href"],
                    "image": img_tag["src"] if img_tag else "",
                    "date": date_tag.get_text(strip=True) if date_tag else ""
                })

        data["categories"].append({
            "name": cat_name,
            "items": items
        })

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_news()
