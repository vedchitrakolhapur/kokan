import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://kokansadlive.com/kokan.html"
ALLOWED_CATEGORIES = [
    "लक्ष्यवेधी", "देश-विदेश", "महाराष्ट्र", 
    "क्राईम", "मनोरंजन", "क्रीडा", "आरोग्य"
]

def scrape_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers, timeout=15)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    data = {
        "updated_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "categories": []
    }

    # १. मुख्य सेक्शन: कोकण -> "ठळक बातम्या"
    main_news = []
    sec1 = soup.find("section", class_="section-1")
    if sec1:
        # मोठी मुख्य बातमी (Left Container)
        left = sec1.find("div", class_="left-container")
        if left:
            a_tag = left.find("a", href=True)
            img_tag = left.find("img")
            title_tag = left.find("h1")
            if a_tag and title_tag:
                main_news.append({
                    "title": title_tag.get_text(strip=True),
                    "link": a_tag["href"],
                    "image": img_tag["src"] if img_tag else "",
                    "date": "ताज्या बातम्या"
                })

        # बाजूच्या ४ बातम्या (Right Container)
        for card in sec1.select(".right-container .news"):
            a_tag = card.find("a", href=True)
            img_tag = card.find("img")
            title_tag = card.find("h6")
            if a_tag and title_tag:
                main_news.append({
                    "title": title_tag.get_text(strip=True),
                    "link": a_tag["href"],
                    "image": img_tag["src"] if img_tag else "",
                    "date": "कोकण"
                })

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