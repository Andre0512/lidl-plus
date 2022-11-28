import re

import requests
from oic import rndstr
from oic.oic import Client
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.utils.settings import OicClientSettings
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver

PHONE = ""
PASSWORD = ""
settings = OicClientSettings()#verify_ssl=False)
client = Client(settings=settings, client_authn_method=CLIENT_AUTHN_METHOD, client_id="LidlPlusNativeClient")
client.provider_config("https://accounts.lidl.com")
code_challenge = client.add_code_challenge()

session = {"state": rndstr(), "nonce": rndstr()}
args = {
    "client_id": client.client_id,
    "response_type": "code",
    "scope": ["openid profile offline_access lpprofile lpapis"],
    # "nonce": session["nonce"],
    "redirect_uri": 'com.lidlplus.app://callback',
    # "state": session["state"]
}
args.update(code_challenge[0])
auth_req = client.construct_AuthorizationRequest(request_args=args)
login_url = auth_req.request(client.authorization_endpoint)
mobile_emulation = {
    "deviceMetrics": {"width": 360, "height": 640, "pixelRatio": 3.0},
    "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19"}
option = webdriver.ChromeOptions()
option.add_argument('headless')
option.add_experimental_option("mobileEmulation", mobile_emulation)
browser = webdriver.Chrome(options=option)
browser.get(f"{login_url}&Country=DE&language=DE-DE")
wait = WebDriverWait(browser, 10)
wait.until(expected_conditions.visibility_of_element_located((By.ID, "button_welcome_login"))).click()
wait.until(expected_conditions.visibility_of_element_located((By.NAME, "EmailOrPhone"))).send_keys(PHONE)
browser.find_element(By.ID, "button_btn_submit_email").click()
browser.find_element(By.ID, "button_btn_submit_email").click()
wait.until(expected_conditions.element_to_be_clickable((By.ID, "field_Password"))).send_keys(PASSWORD)
browser.find_element(By.ID, "button_submit").click()
element = wait.until(expected_conditions.visibility_of_element_located((By.CLASS_NAME, "phone")))
element.find_element(By.TAG_NAME, "button").click()
verify_code = input("Insert token: ")
browser.find_element(By.NAME, "VerificationCode").send_keys(verify_code)
browser.find_element(By.CLASS_NAME, "role_next").click()
code = re.findall("code=([0-9A-F]+)", browser.requests[-1].response.headers.get("Location", ""))[0]
tokenurl = 'https://accounts.lidl.com/connect/token'
headers = {
    'Authorization': 'Basic TGlkbFBsdXNOYXRpdmVDbGllbnQ6c2VjcmV0',
    'Content-Type': 'application/x-www-form-urlencoded'
}
payload = {
    "grant_type": 'authorization_code',
    "code": code,
    "redirect_uri": 'com.lidlplus.app://callback',
    "code_verifier": code_challenge[1]
}
response = requests.post(tokenurl, headers=headers, data=payload)
access_token = response.json()["access_token"]
refresh_token = response.json()["refresh_token"]
print(access_token)
print(refresh_token)
