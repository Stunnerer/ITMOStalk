from html import unescape
from faker import Faker
from bs4 import BeautifulSoup
import pickle
import os
import httpx
import re
import json


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
            self.headers = {
                "User-Agent": self.faker.user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "ru-RU,ru;q=0.9",
                "Priority": "u=0, i",
            }
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
        try:
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
            else:
                return {"success": False, "message": "Invalid email or password"}
        except (httpx.ReadTimeout, httpx.ConnectError):
            return {
                "success": False,
                "message": "Got banned. Use VPN or wait 5-10 minutes.",
            }
        return {"success": True}

    async def update_links(self):
        client = self.client
        resp = await client.get(
            "https://isu.ifmo.ru/", headers=self.headers, follow_redirects=True
        )
        nonce = int(resp.request.url.query.decode().rstrip(":").rsplit(":")[-1])
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

    async def check_auth(self) -> bool:
        client = self.client
        resp = await client.get(
            "https://isu.ifmo.ru/pls/apex/f?p=2143:1:123", headers=self.headers
        )
        if "LOGIN" not in resp.headers["Location"]:
            nonce = int(resp.headers["Location"].rstrip(":").rsplit(":")[-1])
            await self._update_links(nonce)
            return True
        return False

    async def get_group_list(self) -> dict:
        # if "group_list" not in self.links:
        #     await self.update_links()
        # resp = await self.client.get(self.links["group_list"])
        # html = await resp.aread()
        html = open("group_list.html", "r").read()
        soup = BeautifulSoup(html, "html.parser")
        current_tag = soup.select_one(
            'span[data-mustache-template="template-group-grade"]'
        )
        quals = {}
        groups = {}
        group_name = ""
        current_grade = ""
        current_qual = ""
        current_tag = current_tag.find_previous_sibling()
        while True:
            if current_tag.name == "tr":
                tmp_tag = current_tag.findChild(name="span")
                text = unescape(tmp_tag.text)
                text = re.sub("\n +", " ", text)
                j = json.loads(text)
                current_qual = j["qualify"]
                groups = quals[current_qual] = {}
                current_tag = current_tag.find_next_sibling()
                continue
            print(current_tag)
            text = unescape(current_tag.text)
            text = re.sub("\n +", " ", text)
            j = json.loads(text)
            stype = current_tag.attrs["data-mustache-template"]
            if stype == "template-group-faculty":
                groups[
                    group_name := f"[{current_grade}] {j["nameShort"]} ({j["name"]})"
                ] = []
            elif stype == "template-group-group":
                groups[group_name].append((j["group"], j["groupEnc"]))
            elif stype == "template-group-grade":
                current_grade = j["grade"]
            current_tag = current_tag.find_next_sibling()
            if not current_tag:
                break
        return quals

    async def get_potok_list(self) -> dict:
        if "potok_list" not in self.links:
            await self.update_links()
        resp = await self.client.get(self.links["potok_list"])
        html = await resp.aread()
        soup = BeautifulSoup(html, "html.parser")
        groups = {}
        group_name = None
        current_group = []
        current_tag = soup.select_one("span.i_dummy>div.note")
        group_name = current_tag.findChild().text
        group_name = re.sub("\n +", " ", group_name)
        group_name = re.sub(r"\[.+?\] ", "", group_name)
        while True:
            current_tag = current_tag.find_next_sibling()
            if not current_tag:
                break
            if current_tag.name == "div":
                if current_group:
                    groups[group_name] = current_group
                    current_group = []
                group_name = current_tag.findChild().text
                group_name = re.sub("\n +", " ", group_name)
                group_name = re.sub(r"\[.+?\] ", "", group_name)
            else:
                link = current_tag.attrs["href"]
                potok_id = link.rsplit(",")[-2]
                if not potok_id:
                    continue
                potok_name = current_tag.text
                potok_name = re.sub("\n +", " ", potok_name)
                potok_name = re.sub(r"\[.+?\] ", "", potok_name)
                current_group.append((potok_name, potok_id))
        return groups
