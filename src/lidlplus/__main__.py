#!/usr/bin/env python3
import argparse
from getpass import getpass

from lidlplus import LidlPlusApi


def get_arguments():
    """Get parsed arguments."""
    parser = argparse.ArgumentParser(description="Speedport: Command Line Utility")
    subparser = parser.add_subparsers(title="commands", metavar="command", required=True)
    auth = subparser.add_parser("auth", help="Authenticate and get refresh_token")
    auth.add_argument("auth", help="Authenticate and get refresh_token", action="store_true")
    return vars(parser.parse_args())


def print_refresh_token():
    username = input("Enter your lidl plus username (phone number): ")
    password = getpass("Enter your lidl plus password: ")
    language = input("Enter your language (DE, EN, ...): ")
    country = input("Enter your country (de, at, ...): ")
    lidl_plus = LidlPlusApi(language, country)
    lidl_plus.login(username, password, lambda: input("Enter your verify code: "))
    length = len(token := lidl_plus.refresh_token) - len("refresh token")
    print(f"{'-' * (length // 2)} refresh token {'-' * (length // 2 - 1)}\n{token}\n{'-' * len(token)}")


def main():
    args = get_arguments()
    if args.get("auth"):
        print_refresh_token()


if __name__ == '__main__':
    main()
