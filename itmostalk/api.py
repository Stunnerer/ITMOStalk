from faker import Faker
from bs4 import BeautifulSoup
import pickle
import os
import httpx
import re

class API:

    client: httpx.AsyncClient = None
    headers: dict[str, str] = None
    links: dict[str, str] = None
    faker: Faker = None
    authorized = False

    def __init__(self, headers=None):
        self.faker = Faker()
        self.links = {}
        if not headers:
            self.headers = {"User-Agent": self.faker.user_agent()}
        else:
            self.headers = headers
        self.client = httpx.AsyncClient(headers=self.headers)

    async def save_cookies(self):
        with open("cookies.pk", "wb") as f:
            pickle.dump(self.client.cookies.jar._cookies, f)

    async def load_cookies(self):
        if not os.path.isfile("cookies.pk"):
            return None
        cookies = httpx.Cookies()
        with open("cookies.pk", "rb") as f:
            jar_cookies = pickle.load(f)
        for domain, pc in jar_cookies.items():
            for path, c in pc.items():
                for k, v in c.items():
                    cookies.set(k, v.value, domain=domain, path=path)
        self.client.cookies.update(cookies)
        return cookies

    async def get_auth_link(self):
        client = self.client
        cookies = client.cookies

        # get auth page
        resp = await client.get(
            "https://isu.ifmo.ru/pls/apex/f?p=2143:1:", headers=self.headers
        )
        cookies.update(resp.cookies)
        resp = await client.get(resp.headers["Location"], follow_redirects=True)
        cookies.update(resp.cookies)

        # find auth link
        auth_link = re.search(
            r"kc-form-login\".+?action=\"(.+?)\"", resp.text, re.MULTILINE
        ).group(1)
        self.links["auth"] = auth_link

    async def auth(self, email, password):
        client = self.client
        cookies = client.cookies

        if "auth" not in self.links:
            raise RuntimeError("Auth link should be loaded first")
        auth_link = self.links["auth"]
        # authorize using itmo id
        resp = await client.post(
            auth_link,
            headers=self.headers,
            data={
                "username": email,
                "password": password,
                "rememberMe": "on",
                "credentialId": "",
            },
            follow_redirects=True,
        )
        if resp.status_code == 302:
            self.authorized = True
            cookies.update(resp.cookies)
            resp = await client.get(resp.headers["Location"], headers=self.headers)
            cookies.update(resp.cookies)
            nonce = int(resp.request.url.query.rsplit(b":")[-1].decode())
            await self._update_links(nonce)
        return self.authorized

    async def update_links(self):
        client = self.client
        resp = await client.get(
            "https://isu.ifmo.ru/", headers=self.headers, follow_redirects=True
        )
        nonce = int(resp.request.url.query.decode().split(":")[-1])
        await self._update_links(nonce)

    async def _update_links(self, nonce):
        self.links["group_list"] = (
            f"https://isu.ifmo.ru/pls/apex/f?p=2143:9:{nonce}::NO::P9_GR_TYPE:group"
        )
        self.links["potok_list"] = (
            f"https://isu.ifmo.ru/pls/apex/f?p=2143:9:{nonce}::NO::P9_GR_TYPE:potok"
        )
        self.links["group_students"] = (
            f"https://isu.ifmo.ru/pls/apex/f?p=2143:GR:{nonce}::NO::GR_GR,GR_TYPE:{{group_id}},group"
        )
        self.links["potok_students"] = (
            f"https://isu.ifmo.ru/pls/apex/f?p=2143:GR:{nonce}::NO::GR_TYPE,ID_POTOK:potok,{{potok_id}}"
        )
        self.links["potok_schedule"] = (
            f"https://isu.ifmo.ru/pls/apex/f?p=2143:15:{nonce}::NO::SCH,SCH_POTOK_ID,SCH_TYPE:1,{{potok_id}},5"
        )

    async def get_potok_list(self) -> dict:
        if "potok_list" not in self.links:
            await self.update_links()
        # Implement the rest of the method...
