from bs4 import BeautifulSoup
from datetime import datetime
import re
import requests
from urllib.parse import urljoin

EXCHANGE_MAP = {
    "$" : 0.90,
    "£": 1.15
}

base_url = "https://www.avbuyer.com"

def scrape_page():

    page = 1
    aircrafts = []
    run_time = datetime.now().isoformat(timespec="seconds")
    
    while True:
        url = f"https://www.avbuyer.com/aircraft/helicopter/page-{page}"
        r = requests.get(url)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "lxml")

        items = soup.find_all("div", class_="listing-item")

        if not items:
            break 

        for item in items:
            url = urljoin(base_url, item.a.get("href")) 
            brand, model = name_split(item)
            result = price_extraction(item)

            if result is None:
                continue

            currency, eur_price, foreign_price = result

            aircraft = {
                "url": url,
                "brand": brand,
                "model": model,
                "eur_price": eur_price,
                "foreign_price": foreign_price,
                "currency": currency,
                "timestamp": run_time,
                "active": 1
            }

            aircrafts.append(aircraft)
            
        page += 1   
    return aircrafts, run_time    

def name_split(item):
    name = item.find("h2", class_="item-title").get_text(strip=True)
    split = name.split()

    if split[0] == "McDonnell":
        brand = " ".join(split[0:2])
        model = " ".join(split[2:])
    else: 
        brand = split[0]
        model = " ".join(split[1:])
    
    return brand, model

def price_extraction(item):
    price_raw = item.find("div", class_="price").get_text(strip=True)
    tp = re.search(r"([£$€])([\d,]+)", price_raw)

    if not tp:
        return None
    
    currency = tp.group(1)
    orig_price = float(tp.group(2).replace(",", ""))

    if currency == "€":
        eur_price = orig_price
        foreign_price = None
    else:
        eur_price = orig_price * EXCHANGE_MAP[currency]
        foreign_price = orig_price

    return currency, eur_price, foreign_price

