import json
import re
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from datetime import datetime

HOME_URL = "https://kokansadlive.com/kokan.html"
KOKAN_ALL_URL = "https://kokansadlive.com/c/kokan"
YOUTUBE_HANDLE_URL = "https://www.youtube.com/@KokansadLiveNews"

ALLOWED_CATEGORIES = [
    "लक्ष्यवेधी", "देश-विदेश", "महाराष्ट्र",
    "क्राईम", "मनोरंजन", "क्रीडा", "आरोग्य"
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

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
    """@KokansadLiveNews चॅनलचे लेटेस्ट १५ व्हिडिओ काढते"""
    videos = []
    try:
        ch_res = requests.get(
            YOUTUBE_HANDLE_URL,
            headers=HEADERS,
            cookies={"CONSENT": "YES+cb"},
            timeout=15
        )
        match = (
            re.search(r'"channelId":"(UC[\w-]+)"', ch_res.text)
            or re.search(r'channel_id=(UC[\w-]+)', ch_res.text)
        )
        if not match:
            print("YouTube channel ID not found")
            return videos

        channel_id = match.group(1)
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed_res = requests.get(feed_url, headers=HEADERS, timeout=15)
        root = ET.fromstring(feed_res.content)

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015"
        }

        for entry in root.findall("atom:entry", ns)[:15]:
            vid_id_el = entry.find("yt:videoId", ns)
            title_el = entry.find("atom:title", ns)
            pub_el = entry.find("atom:published", ns)

            if vid_id_el is not None and title_el is not None:
                vid_id = vid_id_el.text
                pub_date = ""
                if pub_el is not None and pub_el.text:
                    try:
                        dt = datetime.fromisoformat(pub_el.text.replace("Z", "+00:00"))
                        pub_date = dt.strftime("%d %b %Y")
                    except Exception:
                        pub_date = pub_el.text[:10]

                videos.append({
                    "title": title_el.text.strip(),
                    "link": f"https://www.youtube.com/watch?v={vid_id}",
                    "image": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                    "date": pub_date
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
