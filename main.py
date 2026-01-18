import asyncio
import logging
import time
from urllib.parse import urlparse

import httpx
from selectolax.parser import HTMLParser
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    "Referer": "https://es.investing.com/"
}

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

URL_DEBT_CLOCK = "https://www.usdebtclock.org/world-debt-clock.html"

SPAN_ID_USA = "X2a5BWRG"
SPAN_ID_SPAIN = "J2a1463MMJ"


# --- FUNCTIONS ---

def get_pretty_name(url: str) -> str:
    """Extracts a readable name from the URL slug."""
    slug = urlparse(url).path.split('/')[-1]
    return slug.replace('-', ' ').replace('bond yield', '').title().strip()

async def fetch_yield(client: httpx.AsyncClient, url: str) -> tuple[str, str | None]:
    """Fetches a single yield asynchronously."""
    name = get_pretty_name(url)
    try:
        response = await client.get(url, timeout=15.0)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {name}: Status {response.status_code}")
            return name, None
        
        html = HTMLParser(response.text)
        # Investing.com
        div = html.css_first("div[data-test='instrument-price-last']")
        
        # Fallback selector if the first one fails
        if not div:
            div = html.css_first("span#last_last")
            
        value = div.text(strip=True) if div else None
        return name, value
    except httpx.RequestError as e:
        logger.error(f"Network error for {name}: {e}")
        return name, None
    except Exception as e:
        logger.error(f"Parsing error for {name}: {e}")
        return name, None

async def process_bond_category(title: str, urls: list[str]):
    """Orchestrates the parallel fetching of a list of URLs."""
    print(f"\n📊 Rendimenti per {title}:")
    print("-" * 40)
    
    async with httpx.AsyncClient(headers=HEADERS, http2=True) as client:
       
        tasks = [fetch_yield(client, url) for url in urls]
 
        results = await asyncio.gather(*tasks)
        
        # Sort results by name for cleaner output (optional)
        # results.sort(key=lambda x: x[0])

        for name, value in results:
            if value:
                print(f"{name:<25} : {value:>8}")
            else:
                print(f"{name:<25} :  Error")

async def fetch_debt_clock():
    """Fetches debt clock data using Playwright."""
    print("\n Debt Clock:")
    print("-" * 40)
    
    async with async_playwright() as p:
        # Launch browser with optimization flags
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        
        context = await browser.new_context(user_agent=HEADERS["User-Agent"])
        
        # Block images and fonts to speed up loading
        await context.route("**/*", lambda route: route.abort() 
                            if route.request.resource_type in ["image", "font", "media"] 
                            else route.continue_())

        page = await context.new_page()
        
        try:
            await page.goto(URL_DEBT_CLOCK, timeout=30000, wait_until="domcontentloaded")
            
            # Using asyncio.gather inside Playwright to fetch texts in parallel
            usa_locator = page.locator(f"#{SPAN_ID_USA}")
            spain_locator = page.locator(f"#{SPAN_ID_SPAIN}")
            
            await asyncio.sleep(2) 

            try:
                usa_val = await usa_locator.inner_text(timeout=5000)
            except:
                usa_val = "ID Changed/Not Found"

            try:
                spain_val = await spain_locator.inner_text(timeout=5000)
            except:
                spain_val = "ID Changed/Not Found"

            print(f"{'USA Debt':<25} : {usa_val}")
            print(f"{'Spain Debt':<25} : {spain_val}")

        except Exception as e:
            logger.error(f"Error fetching Debt Clock: {e}")
        finally:
            await browser.close()

async def main():
    start_time = time.time()
    
    
    await process_bond_category("Spagna", URLS_SPAIN)
    await process_bond_category("Italia", URLS_ITALY)
    await process_bond_category("USA", URLS_USA)
    
    await fetch_debt_clock()
    
    duration = time.time() - start_time
    print(f"\n Completato in {duration:.2f} secondi.")

if __name__ == "__main__":
    asyncio.run(main())
