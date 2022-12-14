**This python package is unofficial and is not related in any way to Lidl. It was developed by reversed engineered requests and can stop working at anytime!**

# Python Lidl Plus API
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/Andre0512/lidl-plus/python-check.yml?branch=main&label=checks)](https://github.com/Andre0512/lidl-plus/actions/workflows/python-check.yml)
[![PyPI - Status](https://img.shields.io/pypi/status/lidl-plus)](https://pypi.org/project/lidl-plus)
[![PyPI](https://img.shields.io/pypi/v/lidl-plus?color=blue)](https://pypi.org/project/lidl-plus)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/lidl-plus)](https://www.python.org/)
[![PyPI - License](https://img.shields.io/pypi/l/lidl-plus)](https://github.com/Andre0512/lidl-plus/blob/main/LICENCE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/lidl-plus)](https://pypistats.org/packages/lidl-plus)
  
Fetch receipts and more from Lidl Plus.
## Installation
```bash
pip install lidl-plus
```

## Authentication
To login in Lidl Plus we need to simulate the app login.
This is a bit complicated, we need a web browser and some additional python packages.
After we have received the token once, we can use it for further requestes and we don't need a browser anymore.

#### Prerequisites
* Check you have installed one of the supported web browser
  - Chromium
  - Google Chrome
  - Mozilla Firefox
* Install additional python packages
  ```bash
  pip install "lidl-plus[auth]"
  ```
#### Commandline-Tool
```bash
$ lidl-plus auth
Enter your language (DE, EN, ...): DE
Enter your country (de, at, ...): de
Enter your lidl plus username (phone number): +4915784632296
Enter your lidl plus password:
Enter the verify code you received via phone: 590287
------------------------- refresh token ------------------------
2D4FC2A699AC703CAB8D017012658234917651203746021A4AA3F735C8A53B7F
----------------------------------------------------------------
```

#### Python
```python
from lidlplus import LidlPlusApi

lidl = LidlPlusApi(language="DE", country="de")
lidl.login(phone="+4915784632296", password="password", verify_token_func=lambda: input("Insert code: "))
print(lidl.refresh_token)
```
## Usage
Currently, the only feature is fetching receipts
### Receipts

Get your receipts as json and receive a list of bought items like: 
```json
{
    "currentUnitPrice": "2,19",
    "quantity": "1",
    "isWeight": false,
    "originalAmount": "2,19",
    "extendedAmount": "1,98",
    "description": "Vegane Frikadellen",
    "taxGroup": "1",
    "taxGroupName": "A",
    "codeInput": "4023456245134",
    "discounts": [
        {
            "description": "5??? Coupon",
            "amount": "0,21"
        }
    ],
    "deposit": null,
    "giftSerialNumber": null
},
```

#### Commandline-Tool
```bash
$ lidl-plus --country=de --language=DE --refresh-token=XXXXX receipt --all > data.json
```

#### Python
```python
from lidlplus import LidlPlusApi

lidl = LidlPlusApi("DE", "de", refresh_token="XXXXXXXXXX")
for receipt in lidl.tickets():
    pprint(lidl.ticket(receipt["id"]))
```
