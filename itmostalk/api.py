import asyncio
import datetime
import json
import os
import pickle
import re
import pytz
from html import unescape

import httpx
from bs4 import BeautifulSoup
from faker import Faker
import logging

from itmostalk.db.bindings import Group, Info, Potok, Student, ScheduleEntry, db_session
from itmostalk.db import functions as cache


class API:

    client: httpx.AsyncClient = None
    headers: dict[str, str] = None
    links: dict[str, str] = None
    faker: Faker = None
    authorized = False

    def __init__(self, headers=None):
        self.logger = logging.getLogger("API")
        self._count = 0
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
        with open("data/cookies.pk", "wb") as f:
            pickle.dump(self.client.cookies.jar._cookies, f)

    async def load_cookies(self):
        if not os.path.isfile("data/cookies.pk"):
            return None
        cookies = httpx.Cookies()
        with open("data/cookies.pk", "rb") as f:
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
        self.links["auth"] = unescape(auth_link)

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
        self._count = 0
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
            await asyncio.sleep(0.5)
            await self._update_links(nonce)
            return True
        return False
    
    async def isu_get(self, link, **format):
        if link not in self.links or self._count > 10:
            await self.update_links()
            await asyncio.sleep(0.5)
        resp = await self.client.get(self.links[link].format(**format), follow_redirects=True)
        return await resp.aread()

    async def get_group_list(self) -> dict[str, list[tuple[str, str]]]:
        # html = open("pages_for_test/group_list.html")
        if "group_list" not in self.links:
            await self.update_links()
        html = await self.isu_get("group_list")
        soup = BeautifulSoup(html, "html.parser")
        current_tag = soup.select_one(
            'span[data-mustache-template="template-group-grade"]'
        )
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
                current_qual = j["qualify"][:3]
                current_tag = current_tag.find_next_sibling()
                continue
            text = unescape(current_tag.text)
            text = re.sub("\n +", " ", text)
            j = json.loads(text)
            stype = current_tag.attrs["data-mustache-template"]
            if stype == "template-group-faculty":
                groups.setdefault(
                    group_name := f"[{current_qual} {current_grade}] {j["nameShort"]} ({j["name"]})",
                    [],
                )
            elif stype == "template-group-group":
                groups[group_name].append((j["group"], j["groupEnc"]))
            elif stype == "template-group-grade":
                current_grade = j["grade"]
            current_tag = current_tag.find_next_sibling()
            if not current_tag:
                break
        cache.set_group_list(groups)
        return groups

    def get_people(self, html):
        soup = BeautifulSoup(html, "html.parser")
        tbody = soup.select_one("table.table.table-bordered").select_one("tbody")
        rows = tbody.findChildren("tr")
        for row in rows:
            uid, name = 0, ""
            for td in row.findChildren("td"):
                header = td.attrs["headers"][0]
                if "ИД" in header:
                    uid = int(td.text)
                elif header == "ФИО":
                    name = td.text
                    name = name.strip()
                    name = unescape(name)
                    name = re.sub("\n? +", " ", name)
            yield (uid, name)

    async def get_people_from_group(self, group_id: str):
        # html = open("pages_for_test/group_people.html")
        html = await self.isu_get("group_students", group_id=group_id)
        people = list(self.get_people(html))
        with db_session:
            group = Group.get(id=group_id)
            for uid, name in people:
                student = Student.get(id=uid) or Student(id=uid, name=name)
                group.students.add(student)
        return people

    async def get_potok_list(self) -> dict[str, list[tuple[str, int]]]:
        # html = open("pages_for_test/potok_list.html")
        html = await self.isu_get("potok_list")
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
                    if group_name in groups:
                        group_name += "_"
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
                potok_id = int(potok_id)
                potok_name = current_tag.text
                potok_name = re.sub("\n +", " ", potok_name)
                potok_name = re.sub(r"\[.+?\] ", "", potok_name)
                current_group.append((potok_name, potok_id))
        cache.set_potok_list(groups)
        return groups

    async def get_people_from_potok(self, potok_id: int) -> list:
        # html = open("pages_for_test/potok_people.html")
        html = await self.isu_get("potok_students", potok_id=potok_id)
        people = list(self.get_people(html))
        with db_session:
            group = Potok.get(id=potok_id)
            if group:
                for uid, name in people:
                    student = Student.get(id=uid) or Student(id=uid, name=name)
                    group.students.add(student)
        return people

    async def get_potok_schedule(self, potok_id: int) -> dict:
        # html = open("pages_for_test/potok_schedule.html")z
        html = await self.isu_get("potok_schedule", potok_id=potok_id)
        soup = BeautifulSoup(html, "html.parser")
        current_tag = soup.select_one("table.table.table-bordered").select_one("tr")
        schedule = []
        while current_tag is not None:
            if current_tag.name == "tr":
                td = current_tag.select_one("td")
                if td.attrs.get("id", "") == "ДЕНЬ":
                    h4 = td.findChild("h4")
                    day = h4.text.strip().split(",")[0]
                    self.logger.debug("potok_schedule day: %s", day)
                    day = datetime.datetime.strptime(day, "%d.%m.%Y").date()
                    current_tag = current_tag.find_next_sibling()
                    continue
                else:
                    name = ""
                    while td is not None:
                        if td.attrs.get("headers", [""])[0].startswith("ПАРА"):
                            text = td.getText(strip=True)
                            time_segments = re.findall(r"(\d{1,2}:\d{2})", text)
                            # self.logger.debug("potok_schedule text: %s, segments: %s", text, time_segments)
                            # fmt: off
                            start = datetime.datetime.strptime(
                                time_segments[0], "%H:%M"
                            ).replace(tzinfo=pytz.timezone("Europe/Moscow")).timetz()
                            end = datetime.datetime.strptime(
                                time_segments[1], "%H:%M"
                            ).replace(tzinfo=pytz.timezone("Europe/Moscow")).timetz()
                            # fmt: on
                            self.logger.debug(
                                "potok_schedule time: %s ~ %s", start, end
                            )
                        elif td.attrs.get("headers", [""])[0].startswith("ДИСЦ_НАИМ"):
                            text = td.getText(strip=True)
                            text = re.sub("\n +", " ", text)
                            text = text.strip()
                            name = text
                            self.logger.debug("potok_schedule name: %s", name)
                        elif td.attrs.get("headers", [""])[0].startswith("АУДИТОРИЯ"):
                            text = td.getText(separator="<|>", strip=True)
                            text = re.sub("\n +", " ", text)
                            text = text.strip()
                            if "-" in text:
                                location = "нет аудитории"
                            else:
                                auditorium, place = text.split("<|>")
                                location = f"{place}; ауд. {auditorium}"
                            self.logger.debug("potok_schedule location: %s", location)
                        elif td.attrs.get("headers", [""])[0].startswith("ПРЕПОДАВАТЕЛЬ"):
                            text = td.a.getText(strip=True)
                            text = re.sub("\n +", " ", text)
                            text = text.strip()
                            teacher = text
                            self.logger.debug("potok_schedule teacher: %s", teacher)
                        td = td.find_next_sibling()
                    entry = dict(date=day, start=start, end=end, subject=name, teacher=teacher, location=location)
                    schedule.append(entry)
                    current_tag = current_tag.find_next_sibling()
            elif current_tag.name == "thead":
                current_tag = current_tag.find_next_sibling()
            else:
                current_tag = current_tag.select_one("tr")
        with db_session:
            potok = Potok.get(id=potok_id)
            if potok:
                for entry in schedule:
                    potok.schedule.create(**entry)
        return schedule
