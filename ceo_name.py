import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import time
import stanza


stanza.download('en')


nlp = stanza.Pipeline('en', processors='tokenize,ner')

INPUT_FILE = "clutch_us_it_companies_playwright.csv"
OUTPUT_FILE = "clutch_us_it_companies_with_ceo.csv"

def extract_person_name_stanza(text):
    doc = nlp(text)
    for sentence in doc.sentences:
        for ent in sentence.ents:
            if ent.type == "PERSON":
                return ent.text.strip()
    return None

async def get_ceo(page, company_name):
    query = f"ceo of {company_name}"
    await page.goto("https://www.bing.com/")

    await page.wait_for_selector("textarea#sb_form_q", state="visible", timeout=10000)
    await page.click("textarea#sb_form_q")
    await page.fill("textarea#sb_form_q", "")
    await page.type("textarea#sb_form_q", query, delay=50)
    await page.keyboard.press("Enter")

    await page.wait_for_selector("#b_content", timeout=10000)

    
    bold_texts = await page.locator("strong, b").all_text_contents()
    for text in bold_texts:
        if 2 <= len(text.split()) <= 5:  
            name = extract_person_name_stanza(text)
            if name:
                return name

   
    snippet_bold = await page.locator("#b_results strong, #b_results b").all_text_contents()
    for text in snippet_bold:
        if 2 <= len(text.split()) <= 5:
            name = extract_person_name_stanza(text)
            if name:
                return name

    
    page_text = await page.inner_text("#b_content")
    name = extract_person_name_stanza(page_text)
    if name:
        return name

    return None

async def main():
    df = pd.read_csv(INPUT_FILE)
    if "CEO" not in df.columns:
        df["CEO"] = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        for idx, row in df.iterrows():
            if pd.notna(row["CEO"]):
                continue
            company = row["Name"]
            print(f"Ищу CEO для: {company}")
            try:
                ceo_name = await get_ceo(page, company)
                df.at[idx, "CEO"] = ceo_name
                print(f"Найден CEO: {ceo_name}")
            except Exception as e:
                print(f"Ошибка для {company}: {e}")
            time.sleep(1)

        await browser.close()

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Сохранено в {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())