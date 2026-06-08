from playwright.async_api import async_playwright, Playwright, Page
from playwright_stealth import Stealth
import asyncio
import json
import data_utilities
import random


class Scraper():
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        self.playwright = None
        self.page: Page | None = None
        self.stealth = Stealth()


    async def start(self):
        await self.close()
        
        try:
            self.playwright = await async_playwright().start()
            print("debug: playwright started")

            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                timeout=60000, 
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )  
            print("debug: browser has launched")

            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                locale="en-GB"
            )
            print("debug: context created")

            self.page = await self.context.new_page()
            
            await self.stealth.apply_stealth_async(self.page)
            print("debug: stealth applied to main page")
            
        except Exception as e:
            print(f"Scraping error: {e}")
            await self.close() 
            raise     

    async def run(self, airport):
        location = data_utilities.get_city_from_iata(airport)
        if not location:
            raise ValueError(f"Unknown airport code: {airport}")
        
        clean_location = location.lower()
        replacements = {"ü": "u", "ä": "a", "ö": "o", "ß": "ss", "é": "e", "á": "a"}
        for char, replacement in replacements.items():
            clean_location = clean_location.replace(char, replacement)
            
        clean_location = clean_location.replace(" ", "-")

        url = f"https://www.kiwi.com/en/search/map/{clean_location}/anywhere/?stopNumber=-1%7Efalse&sortBy=price&sortAggregateBy=price"      
        
        # Call the scraper method and return its collected dataset
        return await self.scrape_flights(url)

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

    async def handle_refresh_popup(self, page_instance: Page = None) -> bool:
        """
        An aggressive check for Kiwi's modal 'Refresh' block.
        Bypasses traditional layout constraints using forced clicks.
        """
        target_page = page_instance if page_instance else self.page
        if not target_page:
            return False

        try:
            refresh_btn = target_page.locator("button:has-text('Refresh')").first
            
            if await refresh_btn.count() == 0:
                refresh_btn = target_page.get_by_role("button", name="Refresh").first

            if await refresh_btn.count() > 0:
                await refresh_btn.click(force=True, timeout=2000)
                print("DEBUG: Caught dynamic 'Refresh' pop-up and forced click.")
                await target_page.wait_for_timeout(2500)
                return True
        except Exception:
            pass
        return False        

    async def scroll_down(self):
        for i in range(10):
            await self.handle_refresh_popup()
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
            await self.handle_refresh_popup() 
            await self.scroll_down()
            await self.handle_refresh_popup() 

            cards = self.page.locator('[data-test="PictureCard"]')
            count = await cards.count()
            print(f"DEBUG: Found {count} destination cards")

            if count == 0:
                print("DEBUG: No cards found.")
                return []

            print("DEBUG: Scraping cards sequentially (throttled)...")
            results = []

            # Safeguard iteration boundary limit to 30 elements
            max_loops = min(count, 30)

            for i in range(max_loops):
                await self.handle_refresh_popup()
                
                card = self.page.locator('[data-test="PictureCard"]').nth(i)
                await card.scroll_into_view_if_needed(timeout=5000)

                try:
                    full_name = await card.locator('[data-test="PictureCard-Destination"]').first.inner_text(timeout=4000)
                    dest_name = full_name.strip()
                except:
                    dest_name = "N/A"

                # Extract the link directly from the card element instead of middle clicking
                try:
                    card_link = await card.get_attribute("href", timeout=4000)
                    if not card_link:
                        # Sometimes the href is on a child anchor tag inside the card
                        card_link = await card.locator("a").first.get_attribute("href", timeout=4000)
                    
                    # Resolve relative URLs if necessary
                    if card_link and card_link.startswith("/"):
                        card_link = f"https://www.kiwi.com{card_link}"
                except Exception as link_err:
                    print(f"WARNING: Could not find link for {dest_name}: {link_err}")
                    continue

                if not card_link:
                    print(f"WARNING: No URL found for {dest_name}, skipping.")
                    continue

                print(f"DEBUG: [{i + 1}/{max_loops}] Opening new managed tab for → {dest_name}")

                tab = None
                try:
                    # Explicitly open a clean tab within your context and navigate directly to the link
                    tab = await self.context.new_page()
                    await self.stealth.apply_stealth_async(tab)
                    
                    # Intermittent throttle delay
                    await self.page.wait_for_timeout(random.randint(1500, 3500))
                    
                    # Direct navigation forces the page state to load accurately
                    await tab.goto(card_link, wait_until="domcontentloaded", timeout=45000)
                    await tab.wait_for_load_state("networkidle", timeout=20000)
                    await tab.wait_for_timeout(2000)

                    await self.handle_refresh_popup(page_instance=tab)

                    result_card = tab.locator('[data-test="ResultCardWrapper"]').first
                    
                    if await result_card.count() == 0:
                        print(f"WARNING: Flight details didn't load for {dest_name}")
                        continue

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
                        "index":             i + 1,
                        "departure_iata":    departure_iata.strip(),
                        "departure_full":    "N/A",
                        "destination_iata":  destination_iata.strip(),
                        "destination_full":  dest_name,
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

                    print(f"    Fetched successfully: {result['destination_full']} -> Price: {result['price']}")
                    results.append(result)

                except Exception as e:
                    print(f"WARNING: Tab {i + 1} processing failed: {e}")

                finally:
                    if tab:
                        await tab.close()
                    
                    # Ensure main page is recovered and handled
                    await self.page.bring_to_front()
                    await self.handle_refresh_popup()
                    await self.page.wait_for_timeout(random.randint(2000, 4500))

            with open("kiwi_flights.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4, ensure_ascii=False)

            print(f"Successfully saved {len(results)} destinations to kiwi_flights.json")
            return results

        except Exception as e:
            print(f"ERROR: {e}")
            return []
        finally:
            await self.close()