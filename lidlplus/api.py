import base64
import logging
import re
from datetime import datetime, timedelta

import requests

from lidlplus.exceptions import WebBrowserException, LoginError


class LidlPlusApi:
    _CLIENT_ID = "LidlPlusNativeClient"
    _AUTH_API = "https://accounts.lidl.com"
    _TICKET_API = "https://tickets.lidlplus.com/api/v1"
    _APP = "com.lidlplus.app"
    _OS = "iOs"

    def __init__(self, language, country, refresh_token=""):
        self._login_url = ""
        self._code_verifier = ""
        self._refresh_token = refresh_token
        self._expires = None
        self._token = ""
        self._country = country.upper()
        self._language = language.lower()

    @property
    def refresh_token(self):
        return self._refresh_token

    @property
    def token(self):
        return self._token

    def _register_oauth_client(self):
        from oic.oic import Client
        from oic.utils.authn.client import CLIENT_AUTHN_METHOD

        if self._login_url:
            return self._login_url
        client = Client(
            client_authn_method=CLIENT_AUTHN_METHOD, client_id=self._CLIENT_ID
        )
        client.provider_config(self._AUTH_API)
        code_challenge, self._code_verifier = client.add_code_challenge()
        args = {
            "client_id": client.client_id,
            "response_type": "code",
            "scope": ["openid profile offline_access lpprofile lpapis"],
            "redirect_uri": f"{self._APP}://callback",
            **code_challenge,
        }
        auth_req = client.construct_AuthorizationRequest(request_args=args)
        self._login_url = auth_req.request(client.authorization_endpoint)
        return self._login_url

    def _init_chrome(self, headless=True):
        from seleniumwire import webdriver
        from getuseragent import UserAgent
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service as ChromeService

        user_agent = UserAgent(self._OS.lower()).Random()
        logging.getLogger("WDM").setLevel(logging.NOTSET)
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("headless")
        options.add_experimental_option("mobileEmulation", {"userAgent": user_agent})
        return webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )

    def _init_firefox(self, headless=True):
        from seleniumwire import webdriver
        from getuseragent import UserAgent
        from webdriver_manager.firefox import GeckoDriverManager

        user_agent = UserAgent(self._OS.lower()).Random()
        logging.getLogger("WDM").setLevel(logging.NOTSET)
        options = webdriver.FirefoxOptions()
        if headless:
            options.headless = True
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", user_agent)
        return webdriver.Firefox(
            executable_path=GeckoDriverManager().install(),
            firefox_binary="/usr/bin/firefox",
            options=options,
            firefox_profile=profile,
        )

    def _get_browser(self, headless=True):
        try:
            return self._init_chrome(headless=headless)
        except Exception:
            try:
                return self._init_firefox(headless=headless)
            except Exception:
                raise WebBrowserException

    def _auth(self, payload):
        headers = {
            "Authorization": f'Basic {base64.b64encode(f"{self._CLIENT_ID}:secret".encode()).decode()}',
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(
            f"{self._AUTH_API}/connect/token", headers=headers, data=payload
        ).json()
        self._expires = datetime.utcnow() + timedelta(seconds=response["expires_in"])
        self._token = response["access_token"]
        self._refresh_token = response["refresh_token"]

    def _renew_token(self):
        payload = {"refresh_token": self._refresh_token, "grant_type": "refresh_token"}
        return self._auth(payload)

    def _authorization_code(self, code):
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{self._APP}://callback",
            "code_verifier": self._code_verifier,
        }
        return self._auth(payload)

    def login(
        self, phone, password, verify_token_func, headless=True, verify_mode="phone"
    ):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import TimeoutException

        if verify_mode not in ["phone", "email"]:
            raise ValueError('Only "phone" or "email" supported')
        browser = self._get_browser(headless=headless)
        browser.get(
            f"{self._register_oauth_client()}&Country={self._country}&language={self._language}-{self._country}"
        )
        wait = WebDriverWait(browser, 10)
        wait.until(
            expected_conditions.visibility_of_element_located(
                (By.ID, "button_welcome_login")
            )
        ).click()
        wait.until(
            expected_conditions.visibility_of_element_located((By.NAME, "EmailOrPhone"))
        ).send_keys(phone)
        browser.find_element(By.ID, "button_btn_submit_email").click()
        browser.find_element(By.ID, "button_btn_submit_email").click()
        try:
            wait.until(
                expected_conditions.element_to_be_clickable((By.ID, "field_Password"))
            ).send_keys(password)
            browser.find_element(By.ID, "button_submit").click()
            element = wait.until(
                expected_conditions.visibility_of_element_located(
                    (By.CLASS_NAME, verify_mode)
                )
            )
        except TimeoutException:
            raise LoginError("Wrong credentials")
        element.find_element(By.TAG_NAME, "button").click()
        verify_code = verify_token_func()
        browser.find_element(By.NAME, "VerificationCode").send_keys(verify_code)
        browser.find_element(By.CLASS_NAME, "role_next").click()
        code = re.findall(
            "code=([0-9A-F]+)",
            browser.requests[-1].response.headers.get("Location", ""),
        )[0]
        self._authorization_code(code)

    def _default_headers(self):
        if (
            not self._token and self._refresh_token
        ) or datetime.utcnow() >= self._expires:
            self._renew_token()
        if not self._token:
            raise Exception("You need to login!")
        return {
            "Authorization": f"Bearer {self._token}",
            "App-Version": "999.99.9",
            "Operating-System": self._OS,
            "App": "com.lidl.eci.lidl.plus",
            "Accept-Language": self._language,
        }

    def tickets(self):
        url = f"{self._TICKET_API}/{self._country}/list"
        ticket = requests.get(f"{url}/1", headers=self._default_headers()).json()
        tickets = ticket["records"]
        for i in range(2, int(ticket["totalCount"] / ticket["size"] + 2)):
            tickets += requests.get(
                f"{url}/{i}", headers=self._default_headers()
            ).json()["records"]
        return tickets

    def ticket(self, ticket_id):
        url = f"{self._TICKET_API}/{self._country}/tickets"
        return requests.get(
            f"{url}/{ticket_id}", headers=self._default_headers()
        ).json()
