import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        api_calls = []

        # Intercepter toutes les requêtes réseau
        def on_request(request):
            url = request.url
            # Garder seulement les appels qui ne sont pas des assets
            if not any(x in url for x in [".js", ".css", ".png", ".jpg", ".woff",
                                            "google", "facebook", "analytics"]):
                api_calls.append(f"{request.method} {url}")

        page.on("request", on_request)

        print("Chargement de la page...")
        await page.goto("https://theatrealouest.com/caen/spectacle/liste?sort=date-ASC",
                        wait_until="networkidle", timeout=60000)

        print(f"\nRequêtes API interceptées ({len(api_calls)}):")
        for call in api_calls:
            print(f"  {call}")

        await browser.close()

asyncio.run(main())
