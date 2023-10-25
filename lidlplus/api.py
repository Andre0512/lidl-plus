"""
Lidl Plus api
"""
import base64
import html
import logging
import re
from datetime import datetime, timedelta

import requests

from lidlplus.exceptions import (
    WebBrowserException,
    LoginError,
    LegalTermsException,
    MissingLogin,
)

try:
    from getuseragent import UserAgent
    from oic.oic import Client
    from oic.utils.authn.client import CLIENT_AUTHN_METHOD
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions
    from selenium.webdriver.support.ui import WebDriverWait
    from seleniumwire import webdriver
    from seleniumwire.utils import decode
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
except ImportError:
    pass


class LidlPlusApi:
    """Lidl Plus api connector"""

    _CLIENT_ID = "LidlPlusNativeClient"
    _AUTH_API = "https://accounts.lidl.com"
    _TICKET_API = "https://tickets.lidlplus.com/api/v2"
    _COUPONS_API = "https://coupons.lidlplus.com/api"
    _APP = "com.lidlplus.app"
    _OS = "iOs"
    _TIMEOUT = 10

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
        """Lidl Plus api refresh token"""
        return self._refresh_token

    @property
    def token(self):
        """Current token to query api"""
        return self._token

    def _register_oauth_client(self):
        if self._login_url:
            return self._login_url
        client = Client(client_authn_method=CLIENT_AUTHN_METHOD, client_id=self._CLIENT_ID)
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
        user_agent = UserAgent(self._OS.lower()).Random()
        logging.getLogger("WDM").setLevel(logging.NOTSET)
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("headless")
        options.add_experimental_option("mobileEmulation", {"userAgent": user_agent})
        return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    def _init_firefox(self, headless=True):
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
        # pylint: disable=broad-except
        except Exception as exc1:
            try:
                return self._init_firefox(headless=headless)
            except Exception as exc2:
                raise WebBrowserException from exc1 and exc2

    def _auth(self, payload):
        default_secret = base64.b64encode(f"{self._CLIENT_ID}:secret".encode()).decode()
        headers = {
            "Authorization": f"Basic {default_secret}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        kwargs = {"headers": headers, "data": payload, "timeout": self._TIMEOUT}
        response = requests.post(f"{self._AUTH_API}/connect/token", **kwargs).json()
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

    @property
    def _register_link(self):
        args = {
            "Country": self._country,
            "language": f"{self._language}-{self._country}",
        }
        params = "&".join([f"{key}={value}" for key, value in args.items()])
        return f"{self._register_oauth_client()}&{params}"

    @staticmethod
    def _accept_legal_terms(browser, wait, accept=True):
        wait.until(expected_conditions.visibility_of_element_located((By.ID, "checkbox_Accepted"))).click()
        if not accept:
            title = browser.find_element(By.TAG_NAME, "h2").text
            raise LegalTermsException(title)
        browser.find_element(By.TAG_NAME, "button").click()

    def _parse_code(self, browser, wait, accept_legal_terms=True):
        for request in reversed(browser.requests):
            if f"{self._AUTH_API}/connect" not in request.url:
                continue
            location = request.response.headers.get("Location", "")
            if "legalTerms" in location:
                self._accept_legal_terms(browser, wait, accept=accept_legal_terms)
                return self._parse_code(browser, wait, False)
            if code := re.findall("code=([0-9A-F]+)", location):
                return code[0]
        return ""

    def _click(self, browser, button, request=""):
        del browser.requests
        browser.backend.storage.clear_requests()
        browser.find_element(*button).click()
        self._check_input_error(browser)
        if request and browser.wait_for_request(request, 10):
            self._check_input_error(browser)

    @staticmethod
    def _check_input_error(browser):
        if errors := browser.find_elements(By.CLASS_NAME, "input-error-message"):
            for error in errors:
                if error.text:
                    raise LoginError(error.text)

    def _check_login_error(self, browser):
        response = browser.wait_for_request(f"{self._AUTH_API}/Account/Login.*", 10).response
        body = html.unescape(decode(response.body, response.headers.get("Content-Encoding", "identity")).decode())
        if error := re.findall('app-errors="\\{[^:]*?:.(.*?).}', body):
            raise LoginError(error[0])

    def _check_2fa_auth(self, browser, wait, verify_mode="phone", verify_token_func=None):
        if verify_mode not in ["phone", "email"]:
            raise ValueError(f'Unknown 2fa-mode "{verify_mode}" - Only "phone" or "email" supported')
        response = browser.wait_for_request(f"{self._AUTH_API}/Account/Login.*", 10).response
        if "/connect/authorize/callback" not in response.headers.get("Location"):
            element = wait.until(expected_conditions.visibility_of_element_located((By.CLASS_NAME, verify_mode)))
            element.find_element(By.TAG_NAME, "button").click()
            verify_code = verify_token_func()
            browser.find_element(By.NAME, "VerificationCode").send_keys(verify_code)
            self._click(browser, (By.CLASS_NAME, "role_next"))

    def login(self, phone, password, **kwargs):
        """Simulate app auth"""
        browser = self._get_browser(headless=kwargs.get("headless", True))
        browser.get(self._register_link)
        wait = WebDriverWait(browser, 10)
        wait.until(expected_conditions.visibility_of_element_located((By.ID, "button_welcome_login"))).click()
        wait.until(expected_conditions.visibility_of_element_located((By.NAME, "EmailOrPhone"))).send_keys(phone)
        self._click(browser, (By.ID, "button_btn_submit_email"))
        self._click(
            browser,
            (By.ID, "button_btn_submit_email"),
            request=f"{self._AUTH_API}/api/phone/exists.*",
        )
        wait.until(expected_conditions.element_to_be_clickable((By.ID, "field_Password"))).send_keys(password)
        self._click(browser, (By.ID, "button_submit"))
        self._check_login_error(browser)
        self._check_2fa_auth(
            browser,
            wait,
            kwargs.get("verify_mode", "phone"),
            kwargs.get("verify_token_func"),
        )
        browser.wait_for_request(f"{self._AUTH_API}/connect.*")
        code = self._parse_code(browser, wait, accept_legal_terms=kwargs.get("accept_legal_terms", True))
        self._authorization_code(code)

    def _default_headers(self):
        if (not self._token and self._refresh_token) or datetime.utcnow() >= self._expires:
            self._renew_token()
        if not self._token:
            raise MissingLogin("You need to login!")
        return {
            "Authorization": f"Bearer {self._token}",
            "App-Version": "999.99.9",
            "Operating-System": self._OS,
            "App": "com.lidl.eci.lidl.plus",
            "Accept-Language": self._language,
        }

    def tickets(self, onlyFavorite=False):
        """
        Get a list of all tickets.

        :param onlyFavorite: A boolean value indicating whether to only retrieve favorite tickets.
            If set to True, only favorite tickets will be returned.
            If set to False (the default), all tickets will be retrieved.
        :type onlyFavorite: bool
        """
        url = f"{self._TICKET_API}/{self._country}/tickets"
        kwargs = {"headers": self._default_headers(), "timeout": self._TIMEOUT}
        ticket = requests.get(f"{url}?pageNumber=1&onlyFavorite={onlyFavorite}", **kwargs).json()
        tickets = ticket["tickets"]
        for i in range(2, int(ticket["totalCount"] / ticket["size"] + 2)):
            tickets += requests.get(f"{url}?pageNumber={i}", **kwargs).json()["tickets"]
        return tickets

    def ticket(self, ticket_id):
        """Get full data of single ticket by id"""
        kwargs = {"headers": self._default_headers(), "timeout": self._TIMEOUT}
        url = f"{self._TICKET_API}/{self._country}/tickets"
        return requests.get(f"{url}/{ticket_id}", **kwargs).json()

    def coupons(self):
        """Get list of all coupons"""
        url = f"{self._COUPONS_API}/v2/{self._country}"
        kwargs = {"headers": self._default_headers(), "timeout": self._TIMEOUT}
        return requests.get(url, **kwargs).json()

    def activate_coupon(self, coupon_id):
        """Activate single coupon by id"""
        url = f"{self._COUPONS_API}/v1/{self._country}/{coupon_id}/activation"
        kwargs = {"headers": self._default_headers(), "timeout": self._TIMEOUT}
        return requests.post(url, **kwargs).json()

    def deactivate_coupon(self, coupon_id):
        """Deactivate single coupon by id"""
        url = f"{self._COUPONS_API}/v1/{self._country}/{coupon_id}/activation"
        kwargs = {"headers": self._default_headers(), "timeout": self._TIMEOUT}
        return requests.delete(url, **kwargs).json()
