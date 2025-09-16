import asyncio
import logging
import sys

from itmostalk.api import API
from itmostalk.tui.app import ITMOStalkApp
from itmostalk.db.bindings import Base

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)


async def run_tui():
    app = ITMOStalkApp()
    await app.run_async()


async def run_test():
    api = API()
    if not await api.load_cookies():
        await api.get_auth_link()
        print("throttling")
        await asyncio.sleep(3)
        await api.auth(input(), input())
        await api.save_cookies()
        await asyncio.sleep(3)
    # await api.update_links()
    # await api.client.get(api.links["group_list"], headers=HEADERS)
    quals = await api.get_potok_list()
    quals1 = await api.get_potok_schedule(63176)
    print(quals1)
    # print(quals == quals1)
    # quals = await api.get_potok_schedule(1)
    # print(quals)

    # print(await api.get_people_from_potok("qwe"))


async def main():
    if "test" in sys.argv:
        await run_test()
    else:
        await run_tui()