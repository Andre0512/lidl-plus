**This python package is unofficial and is not related in any way to Lidl. It was developed by reversed engineered requests and can stop working at anytime!**

# Python Lidl Plus API
## Installation
```commandline
pip install lidl-plus
```

## Generate refresh token

#### Prerequisites
You need to install *Google Chrome* and some additional python packages to generate.
```commandline
pip install "lidl-plus[auth]"
```
#### Commandline-Tool
You can use the commandline tool `lidl-plus` to generate a Lidl Plus refresh token once on a device with Google Chrome.
```commandline
$ lidl-plus auth
Enter your lidl plus username (phone number): +4915784632296
Enter your lidl plus password: 
Enter your language (DE, EN, ...): DE
Enter your country (de, at, ...): de
Enter your verify code: 590287
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
#### Get tickets
```python
from lidlplus import LidlPlusApi

lidl = LidlPlusApi("DE", "de", refresh_token="XXXXXXXXXX")
for ticket in lidl.tickets():
    print(lidl.ticket(ticket["id"]))
```
