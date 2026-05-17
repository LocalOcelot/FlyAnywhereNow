from playwright.async_api import async_playwright, Playwright, Page
import asyncio
import json

AIRPORT_LOCATIONS = {
    "ABZ": "aberdeen",
    "EDI": "edinburgh",
    "GLA": "glasgow",
    "INV": "inverness",
    "PIK": "prestwick",
    "DND": "dundee"
}

class Scraper():
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        self.page: Page | None = None


    async def start(self):
        await self.close()
        
        try:
            self.playwright = await async_playwright().start()
            print("debug: playwright started")

            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                timeout=60000, 
                args=["--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=AutomationControlled",]
            )  
            print("debug: browser has launched")

            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                locale="en-GB"
            )
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)
            print("debug: context created")

            self.page = await self.context.new_page()
            print("debug: new page created")
            
        except Exception as e:
            print(f"Scraping error: {e}")
            await self.close() 
            raise     

    async def run(self, airport="ABZ"):
        location = self.AIRPORT_LOCATIONS.get(airport, "aberdeen")
        base_url = os.getenv("SCRAPE_BASE_URL")
        params = os.getenv("SCRAPE_PARAMS")
        url = f"{base_url}/{location}-united-kingdom/anywhere/{params}"
        await self.scrape_flights(url)        

    async def close(self):
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass  
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            
    async def handle_cookies(self):
        try:
            reject_btn = self.page.get_by_role("button", name="Reject all")
            if await reject_btn.is_visible(timeout=5000):
                await reject_btn.click()
                print("DEBUG: Rejected cookies")
                await self.page.wait_for_timeout(1000)
        except:
            print("DEBUG: No cookie banner found")

    async def scroll_down(self):
        for _ in range(10):
            await self.page.evaluate("window.scrollBy(0, 800)")
            await self.page.wait_for_timeout(500)
        print("DEBUG: Finished scrolling")

    async def scrape_flights(self, url: str):  
        print(f"DEBUG: Starting Kiwi.com scrape → {url}")
        await self.start()

        try:
            print("DEBUG: Navigating to page...")
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            await self.page.wait_for_timeout(6000)

            await self.handle_cookies()
            await self.scroll_down()

            cards = self.page.locator('[data-test="PictureCard"]')
            count = await cards.count()
            print(f"DEBUG: Found {count} destination cards")

            if count == 0:
                print("DEBUG: No cards found.")
                return

            print("DEBUG: Opening all cards in new tabs...")
            destination_names = {}
            for i in range(count):
                card = self.page.locator('[data-test="PictureCard"]').nth(i)
                await card.scroll_into_view_if_needed(timeout=5000)

                try:
                    full_name = await card.locator('[data-test="PictureCard-Destination"]').first.inner_text(timeout=4000)
                    destination_names[i + 1] = full_name.strip()
                except:
                    destination_names[i + 1] = "N/A"

                await card.click(button="middle")
                await self.page.wait_for_timeout(1000)

            print(f"DEBUG: Opened {count} tabs, starting scrape...")

            results = []

            for i, tab in enumerate(self.context.pages[1:], start=1):
                try:
                    await tab.bring_to_front()
                    await tab.wait_for_load_state("networkidle", timeout=20000)
                    await tab.wait_for_timeout(2000)

                    print(f"DEBUG: [{i}/{count}] Scraping tab → {tab.url}")

                    result_card = tab.locator('[data-test="ResultCardWrapper"]').first
                    outbound_sector = result_card.locator('[data-test="ResultCardSectorWrapper"]').first

                    try:
                        departure_iata   = await outbound_sector.locator('[data-test="stationName"]').first.inner_text(timeout=4000)
                        destination_iata = await outbound_sector.locator('[data-test="stationName"]').last.inner_text(timeout=4000)
                    except:
                        departure_iata = destination_iata = "N/A"

                    try:
                        price = await result_card.locator('[data-test="ResultCardPrice"] span').first.inner_text(timeout=4000)
                    except:
                        price = "N/A"

                    try:
                        airline = await result_card.locator('[data-test="ResultCardCarrierLogo"] img').first.get_attribute("alt", timeout=4000)
                    except:
                        airline = "N/A"

                    try:
                        timestamps = result_card.locator('[data-test="TripTimestamp"] time')
                        outbound_dep = await timestamps.nth(0).inner_text(timeout=4000)
                        outbound_arr = await timestamps.nth(1).inner_text(timeout=4000)
                        return_dep   = await timestamps.nth(2).inner_text(timeout=4000)
                        return_arr   = await timestamps.nth(3).inner_text(timeout=4000)
                    except:
                        outbound_dep = outbound_arr = return_dep = return_arr = "N/A"

                    try:
                        dates = result_card.locator('[data-test="ResultCardSectorDepartureDate"] time')
                        outbound_date = await dates.nth(0).inner_text(timeout=4000)
                        return_date   = await dates.nth(1).inner_text(timeout=4000)
                    except:
                        outbound_date = return_date = "N/A"

                    try:
                        durations = result_card.locator('.orbit-badge time')
                        outbound_duration = await durations.nth(0).inner_text(timeout=4000)
                        return_duration   = await durations.nth(1).inner_text(timeout=4000)
                    except:
                        outbound_duration = return_duration = "N/A"

                    try:
                        outbound_stops = await result_card.locator('[data-test="StopCountBadge-0"]').nth(0).inner_text(timeout=4000)
                        return_stops   = await result_card.locator('[data-test="StopCountBadge-0"]').nth(1).inner_text(timeout=4000)
                    except:
                        outbound_stops = return_stops = "N/A"

                    result = {
                        "index":             i,
                        "departure_iata":    departure_iata.strip(),
                        "departure_full":    "N/A",
                        "destination_iata":  destination_iata.strip(),
                        "destination_full":  destination_names.get(i, "N/A"),
                        "price":             price.strip(),
                        "airline":           airline.strip() if airline else "N/A",
                        "outbound_date":     outbound_date.strip(),
                        "outbound_dep":      outbound_dep.strip(),
                        "outbound_arr":      outbound_arr.strip(),
                        "outbound_duration": outbound_duration.strip(),
                        "outbound_stops":    outbound_stops.strip(),
                        "return_date":       return_date.strip(),
                        "return_dep":        return_dep.strip(),
                        "return_arr":        return_arr.strip(),
                        "return_duration":   return_duration.strip(),
                        "return_stops":      return_stops.strip(),
                    }

                    print(f"    {result}")
                    results.append(result)

                except Exception as e:
                    print(f"WARNING: Tab {i} failed: {e}")

                finally:
                    await tab.close()

            with open("kiwi_flights.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4, ensure_ascii=False)

            print(f"Successfully saved {len(results)} destinations to kiwi_flights.json")

        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await self.close()


