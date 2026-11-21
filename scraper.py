import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

HOME_URL = "https://kokansadlive.com/kokan.html"
KOKAN_ALL_URL = "https://kokansadlive.com/c/kokan"

ALLOWED_CATEGORIES = [
    "लक्ष्यवेधी", "देश-विदेश", "महाराष्ट्र",
    "क्राईम", "मनोरंजन", "क्रीडा", "आरोग्य"
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def scrape_kokan_all():
    """https://kokansadlive.com/c/kokan वरून सर्व बातम्या काढते"""
    items = []
    seen_links = set()
    try:
        res = requests.get(KOKAN_ALL_URL, headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # पेजवरील सर्व बातम्यांचे कार्ड्स शोधणे
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "/kokan/" not in href or href in seen_links:
                continue

            # लिंकच्या आत किंवा पालक घटकात इमेज आणि टायटल शोधणे
            parent = a_tag.parent
            img_tag = a_tag.find("img") or (parent.find("img") if parent else None)
            
            title_tag = (
                a_tag.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                or a_tag
            )
            title = title_tag.get_text(" ", strip=True)

            if not title or len(title) < 10:
                continue

            # तारीख शोधणे (असल्यास)
            date_text = "कोकण"
            if parent:
                p_tag = parent.find("p")
                if p_tag and len(p_tag.get_text(strip=True)) < 25:
                    date_text = p_tag.get_text(strip=True)

            seen_links.add(href)
            items.append({
                "title": title,
                "link": href if href.startswith("http") else f"https://kokansadlive.com{href}",
                "image": img_tag["src"] if img_tag and img_tag.get("src") else "",
                "date": date_text
            })
    except Exception as e:
        print("Error scraping /c/kokan:", e)

    return items

def scrape_news():
    response = requests.get(HOME_URL, headers=HEADERS, timeout=15)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    data = {
        "updated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "categories": []
    }

    # १. मुख्य सेक्शन: /c/kokan मधील सर्व बातम्या ("ठळक बातम्या")
    main_news = scrape_kokan_all()
    data["categories"].append({
        "name": "ठळक बातम्या",
        "items": main_news
    })

    # २. इतर कॅटेगरी (section.blogs)
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
