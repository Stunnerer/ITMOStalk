from keycloak import KeycloakOpenID
import httpx
import aiohttp
import re
import logging
from time import sleep
from itmostalk.api import API
from itmostalk.tui import ITMOStalkApp

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)


HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Priority": "u=0, i",
}

async def main():
    app = ITMOStalkApp()
    await app.run_async()


async def _main():
    api = API(headers=HEADERS)
    if not await api.load_cookies():
        await api.get_auth_link()
        print("throttling")
        await asyncio.sleep(3)
        await api.auth(input(), input())
        await api.save_cookies()
        await asyncio.sleep(3)
    await api.update_links()