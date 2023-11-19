#!/usr/bin/env python3
"""
lidl plus command line tool
"""
import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path
from datetime import datetime

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
# pylint: disable=wrong-import-position
from lidlplus import LidlPlusApi
from lidlplus.exceptions import WebBrowserException, LoginError, LegalTermsException


def get_arguments():
    """Get parsed arguments."""
    parser = argparse.ArgumentParser(
        prog="lidl-plus",
        description="Lidl Plus API",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=28),
    )
    parser.add_argument("-c", "--country", metavar="CC", help="country (DE, BE, NL, AT, ...)")
    parser.add_argument("-l", "--language", metavar="LANG", help="language (de, en, fr, it, ...)")
    parser.add_argument("-u", "--user", help="Lidl Plus login username")
    parser.add_argument("-p", "--password", metavar="XXX", help="Lidl Plus login password")
    parser.add_argument(
        "--2fa",
        choices=["phone", "email"],
        default="phone",
        help="choose two factor auth method",
    )
    parser.add_argument("-r", "--refresh-token", metavar="TOKEN", help="refresh token to authenticate")
    parser.add_argument("--skip-verify", help="skip ssl verification", action="store_true")
    parser.add_argument(
        "--not-accept-legal-terms",
        help="not auto accept legal terms updates",
        action="store_true",
    )
    parser.add_argument("-d", "--debug", help="debug mode", action="store_true")
    subparser = parser.add_subparsers(title="commands", metavar="command", required=True)
    auth = subparser.add_parser("auth", help="authenticate and get token")
    auth.add_argument("auth", help="authenticate and print refresh_token", action="store_true")
    loyalty_id = subparser.add_parser("id", help="show loyalty ID")
    loyalty_id.add_argument("id", help="show loyalty ID", action="store_true")
    receipt = subparser.add_parser("receipt", help="output last receipts as json")
    receipt.add_argument("receipt", help="output last receipts as json", action="store_true")
    receipt.add_argument("-a", "--all", help="fetch all receipts", action="store_true")
    coupon = subparser.add_parser("coupon", help="activate coupons")
    coupon.add_argument("coupon", help="output all coupons", action="store_true")
    coupon.add_argument("-a", "--all", help="activate all coupons", action="store_true")
    return vars(parser.parse_args())


def check_auth():
    """check auth package is installed"""
    try:
        # pylint: disable=import-outside-toplevel, unused-import
        import oic
        import seleniumwire
        import getuseragent
        import webdriver_manager
    except ImportError:
        print(
            "To login and receive a refresh token you need to install all auth requirements:\n"
            '  pip install "lidl-plus[auth]"\n'
            "You also need google chrome to be installed."
        )
        sys.exit(1)


def lidl_plus_login(args):
    """handle authentication"""
    if not args.get("refresh_token"):
        check_auth()
    if args.get("skip_verify"):
        os.environ["WDM_SSL_VERIFY"] = "0"
        os.environ["CURL_CA_BUNDLE"] = ""
    language = args.get("language") or input("Enter your language (de, en, ...): ")
    country = args.get("country") or input("Enter your country (DE, AT, ...): ")
    if args.get("refresh_token"):
        return LidlPlusApi(language, country, args.get("refresh_token"))
    username = args.get("user") or input("Enter your lidl plus username (phone number): ")
    password = args.get("password") or getpass("Enter your lidl plus password: ")
    lidl_plus = LidlPlusApi(language, country)
    try:
        text = f"Enter the verify code you received via {args['2fa']}: "
        lidl_plus.login(
            username,
            password,
            verify_token_func=lambda: input(text),
            verify_mode=args["2fa"],
            headless=not args.get("debug"),
            accept_legal_terms=not args.get("not_accept_legal_terms"),
        )
    except WebBrowserException:
        print("Can't connect to web browser. Please install Chrome, Chromium or Firefox")
        sys.exit(101)
    except LoginError as error:
        print(f"Login failed - {error}")
        sys.exit(102)
    except LegalTermsException as error:
        print(f"Legal terms not accepted - {error}")
        sys.exit(103)
    return lidl_plus


def print_refresh_token(args):
    """pretty print refresh token"""
    lidl_plus = lidl_plus_login(args)
    length = len(token := lidl_plus.refresh_token) - len("refresh token")
    print(f"{'-' * (length // 2)} refresh token {'-' * (length // 2 - 1)}\n" f"{token}\n" f"{'-' * len(token)}")


def print_loyalty_id(args):
    """print loyalty ID"""
    lidl_plus = lidl_plus_login(args)
    print(lidl_plus.loyalty_id())


def print_tickets(args):
    """pretty print as json"""
    lidl_plus = lidl_plus_login(args)
    if args.get("all"):
        tickets = [lidl_plus.ticket(ticket["id"]) for ticket in lidl_plus.tickets()]
    else:
        tickets = lidl_plus.ticket(lidl_plus.tickets()[0]["id"])
    print(json.dumps(tickets, indent=4))


def activate_coupons(args):
    """Activate all available coupons"""
    lidl_plus = lidl_plus_login(args)
    coupons = lidl_plus.coupons()
    if not args.get("all"):
        print(json.dumps(coupons, indent=4))
        return
    i = 0
    for section in coupons.get("sections", {}):
        for coupon in section.get("coupons", {}):
            if coupon["isActivated"]:
                continue
            if datetime.fromisoformat(coupon["startValidityDate"]) > datetime.now():
                continue
            if datetime.fromisoformat(coupon["endValidityDate"]) < datetime.now():
                continue
            print("activating coupon: ", coupon["title"])
            lidl_plus.activate_coupon(coupon["id"])
            i += 1
    print(f"Activated {i} coupons")


def main():
    """argument commands"""
    args = get_arguments()
    if args.get("auth"):
        print_refresh_token(args)
    elif args.get("id"):
        print_loyalty_id(args)
    elif args.get("receipt"):
        print_tickets(args)
    elif args.get("coupon"):
        activate_coupons(args)


def start():
    """wrapper for cmd tool"""
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted.")


if __name__ == "__main__":
    start()
