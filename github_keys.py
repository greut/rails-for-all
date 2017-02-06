#!/usr/bin/env python3
"""
Github keys
-----------

Downloads the ssh keys from github.
"""

import csv
import json
import os
import re
import requests
import sys
import unicodedata

__author__ = "Yoan Blanc <yoan@dosimple.ch>"
__version__ = "0.3.0"


def format_user_name(firstname, lastname, special=False):
    """Format the real name into a username

    E.g.: Juan Giovanni Di Sousa Santos -> juan
    """
    # Keep only the first if not special
    first = re.match("^(.+?)\\b", firstname, re.U).group(0).lower()
    if special:
        first += lastname[0].lower()

    username = unicodedata.normalize("NFD", first)
    username = username.replace(" ", "")
    # http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string/517974#517974
    return "".join([c for c in username if not unicodedata.combining(c)])


def github_keys(username, auth=None):
    output = []
    # Create authorized_keys
    r = requests.get("https://api.github.com/users/{0}/keys".format(username),
                     auth=auth)
    if r.ok:
        keys = r.json()
        for key in keys:
            yield "{} {}@{}".format(key["key"], username, key["id"])

        if not len(keys):
            print("No keys for @{0}".format(username), file=sys.stderr)

    else:
        print(
            "Cannot grab github key of {0}".format(username), file=sys.stderr)


def main(argv):
    github_user = argv[1] if len(argv) > 1 else None
    github_key = argv[2] if len(argv) > 2 else None

    users = {}

    reader = csv.reader(sys.stdin, delimiter="\t")
    # skip headers
    next(reader)
    for row in reader:
        firstname = row[1]
        lastname = row[0]
        username = format_user_name(firstname, lastname,
                                    firstname in ("Cyril", "Julien"))
        github = row[4]
        if not github:
            continue
        if username in users:
            print(
                "This username already exists {0}".format(username),
                file=sys.stderr)

        users[username] = {
            "firstname": firstname,
            "lastname": lastname,
            "github": github,
            "email": row[2],
            "classname": row[3],
            "keys":
            [key for key in github_keys(github, (github_user, github_key))]
        }

    json.dump(users, sys.stdout, sort_keys=True, indent=2)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
