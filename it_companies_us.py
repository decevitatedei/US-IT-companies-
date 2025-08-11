import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import pandas as pd
import time
import os

def get_real_url(redirect_url):
    parsed = urllib.parse.urlparse(redirect_url)
    params = urllib.parse.parse_qs(parsed.query)
    if 'u' in params:
        return urllib.parse.unquote(params['u'][0])
    return redirect_url

async def scrape_page(page):
    companies = []
    cards = await page.query_selector_all('.provider')
    for card in cards:
        
        name_tag = await card.query_selector('a.provider__title-link.directory_profile')
        name = await name_tag.inner_text() if name_tag else None
        name = name.strip() if name else None

        
        location_tag = await card.query_selector('div.provider__highlights-item.location')
        location = await location_tag.inner_text() if location_tag else None
        location = location.strip() if location else None

        
        website_tag = await card.query_selector('a.website-link__item')
        website_href = await website_tag.get_attribute('href') if website_tag else None
        website = get_real_url(website_href) if website_href else None

        companies.append({
            "Name": name,
            "Location": location,
            "Website": website
        })
    return companies

async def main():
    max_companies = 80
    page_num = 0
    filename = "clutch_us_it_companies_playwright.csv"

    
    existing_websites = set()
    if os.path.exists(filename):
        df_existing = pd.read_csv(filename)
        existing_websites = set(df_existing["Website"].dropna().tolist())
        print(f"В файле уже есть {len(existing_websites)} уникальных сайтов.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  
        context = await browser.new_context()
        page = await context.new_page()

        while True:
            url = f"https://clutch.co/us/it-services?page=1"
            print(f"Парсим страницу {page_num}: {url}")
            await page.goto(url)
            await page.wait_for_selector('.provider')

            companies = await scrape_page(page)

            
            new_companies = [c for c in companies if c["Website"] not in existing_websites and c["Website"]]

            if not new_companies:
                print("Новых компаний на этой странице нет.")
            else:
                
                df_new = pd.DataFrame(new_companies)
                df_new.to_csv(filename, mode="a", index=False, header=not os.path.exists(filename))
                print(f"Добавлено компаний: {len(new_companies)}")

                
                existing_websites.update([c["Website"] for c in new_companies])

            if len(existing_websites) >= max_companies:
                print("Достигли лимита компаний.")
                break

            page_num += 1
            time.sleep(1)

        await browser.close()

    print(f"Данные сохранены в {filename}")

if __name__ == "__main__":
    asyncio.run(main())