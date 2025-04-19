import httpx
from selectolax.parser import HTMLParser
import asyncio
from playwright.async_api import async_playwright

# URL
URLS_SPAIN = [
    "https://es.investing.com/rates-bonds/spain-9-month",
    "https://es.investing.com/rates-bonds/spain-6-month-bond-yield",
    "https://es.investing.com/rates-bonds/spain-3-month-bond-yield",
    "https://es.investing.com/rates-bonds/spain-30-year-bond-yield",
    "https://es.investing.com/rates-bonds/spain-25-year",
    "https://es.investing.com/rates-bonds/spain-20-year-bond-yield",
    "https://es.investing.com/rates-bonds/spain-15-year-bond-yield",
    "https://es.investing.com/rates-bonds/spain-10-year-bond-yield",
    "https://es.investing.com/rates-bonds/spain-9-year-bond-yield",
    "https://es.investing.com/rates-bonds/spain-5-year-bond-yield",
    "https://es.investing.com/rates-bonds/spain-4-year-bond-yield",
    "https://es.investing.com/rates-bonds/spain-3-year-bond-yield",
    "https://es.investing.com/rates-bonds/spain-2-year-bond-yield",
    "https://es.investing.com/rates-bonds/spain-1-year-bond-yield"
]

URLS_ITALY = [
    "https://es.investing.com/rates-bonds/italy-3-month-bond-yield",
    "https://es.investing.com/rates-bonds/italy-1-month",
    "https://es.investing.com/rates-bonds/italy-30-year",
    "https://es.investing.com/rates-bonds/italy-10-year-bond-yield",
    "https://es.investing.com/rates-bonds/italy-5-year-bond-yield",
    "https://es.investing.com/rates-bonds/italy-4-year-bond-yield",
    "https://es.investing.com/rates-bonds/italy-3-year-bond-yield",
    "https://es.investing.com/rates-bonds/italy-2-year-bond-yield",
    "https://es.investing.com/rates-bonds/italy-1-year-bond-yield"
]

URLS_USA = [
    "https://es.investing.com/rates-bonds/u.s.-1-month-bond-yield",
    "https://es.investing.com/rates-bonds/u.s.-3-month-bond-yield",
    "https://es.investing.com/rates-bonds/u.s.-6-month-bond-yield",
    "https://es.investing.com/rates-bonds/u.s.-1-year-bond-yield",
    "https://es.investing.com/rates-bonds/u.s.-2-year-bond-yield",
    "https://es.investing.com/rates-bonds/u.s.-3-year-bond-yield",
    "https://es.investing.com/rates-bonds/u.s.-5-year-bond-yield",
    "https://es.investing.com/rates-bonds/u.s.-7-year-bond-yield",
    "https://es.investing.com/rates-bonds/u.s.-10-year-bond-yield",
    "https://es.investing.com/rates-bonds/u.s.-30-year-bond-yield"
]

# URL Debt Clock
URL_DEBT_CLOCK = "https://www.usdebtclock.org/world-debt-clock.html"
SPAN_ID_USA = "X2a5BWRG"
SPAN_ID_SPAIN = "J2a1463MMJ"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def extract_yield(url):
    try:
        response = httpx.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        html = HTMLParser(response.text)
        div = html.css_first("div[data-test='instrument-price-last']")
        return div.text(strip=True) if div else None
    except Exception:
        return None

def print_yields(title, urls):
    print(f"\n📊 Rendimenti per {title}:\n" + "-"*30)
    for url in urls:
        name = url.split("/")[-1]
        yield_value = extract_yield(url)
        print(f"{name}: {yield_value if yield_value else '❌ Non trovato'}")

async def fetch_debt_clock():
    print("\n💰 Debt Clock:\n" + "-"*30)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL_DEBT_CLOCK)

        try:
            usa = await page.inner_text(f"span#{SPAN_ID_USA}")
        except:
            usa = "❌ Non trovato"

        try:
            spain = await page.inner_text(f"span#{SPAN_ID_SPAIN}")
        except:
            spain = "❌ Non trovato"

        print(f"USA: {usa}")
        print(f"Spagna: {spain}")
        await browser.close()

if __name__ == "__main__":
    print_yields("Spagna", URLS_SPAIN)
    print_yields("Italia", URLS_ITALY)
    print_yields("USA", URLS_USA)
    asyncio.run(fetch_debt_clock())
