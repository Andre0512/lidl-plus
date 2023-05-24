"""
Exeptions
"""


class WebBrowserException(Exception):
    """No Browser installed"""


class LoginError(Exception):
    """Login failed"""


class LegalTermsException(Exception):
    """Not accepted legal terms"""


class MissingLogin(Exception):
    """Login necessary"""
