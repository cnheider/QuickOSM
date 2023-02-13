#!/usr/bin/env python3

import json

from datetime import date
from os import path
from sys import argv

import requests

# This script downloads the statistics of localization of the project from Transifex.
# To be able to use it, you need to provide your user account token
# and run `python3 scripts/load_tx_stats.py <TX_TOKEN> <ORGANIZATION optional> <PROJECT optional>`
# from the repo main folder

LANGUAGE_MAP = {
    'nl': '🇳🇱',
    'fr': '🇫🇷',
    'zh': '🇨🇳',
    'it': '🇮🇹',
    'uk': '🇺🇦',
    'de': '🇩🇪',
    'zh_TW': '🇹🇼',
    'fi': '🇫🇮',
    'ko': '🇰🇷',
    'pt_BR': '🇧🇷',
    'ro': '🇷🇴',
    'id': '🇮🇩',
    'pl': '🇵🇱',
    'es': '🇪🇸',
    'vi': '🇻🇳',
    'ru': '🇷🇺',
    'he': '🇮🇱',
    'da': '🇳🇱',
    'pt': '🇵🇹',
    'sv': '🇸🇪',
}

# Catch the Transifex api token value (passed as argument to the python command)
if len(argv) <= 1:
    print("Missing transifex token argument")
    exit(1)

TX_TOKEN = argv[1]
#
# if len(argv) == 4:
#     ORGANIZATION = argv[2]
#     PROJECT = argv[3]
# else:
#     ORGANIZATION = 'qgis'
#     PROJECT = 'qgis-documentation'

ORGANIZATION = 'quickosm'
PROJECT = 'gui'

# Load stats of the given project from transifex
url = f'https://api.transifex.com/organizations/{ORGANIZATION}/projects/{PROJECT}/'
response = requests.get(url, auth=('Bearer', TX_TOKEN))
if response.status_code == 404:
    raise Exception(f'Error HTTP 404 from the call to "{url}" with the given token.')

data = response.json()

# Get statistics of translation for each target language
language_rate = {}

# Fetch list of languages
for lang in data['languages']:
    code = lang['code']
    name = lang['name']
    language_rate[code] = name

# Fetch and store stats of interest for each target language
for code in data['stats']:
    language_rate[code] = {
        'name': language_rate[code],
        'percentage': round(data['stats'][code]['translated']['percentage'] * 100, 2)
    }

# Stats for the whole project (== English source language)
# Number of languages declared in transifex for the project
nb_languages = len(data['languages'])
# Total number of strings in English to translate
totalstringcount = data['stringcount']
# translation percentage of the whole project
translation_ratio = round(
    sum(
        [value['percentage'] for value in language_rate.values()]
    ) / nb_languages,
    2
)

language_rate['en'] = {
    'nb_languages': nb_languages,
    'stringcount': totalstringcount,
    'percentage': translation_ratio
}


def load_overall_stats():
    """Format statistics of translation in the project"""

    text = (
        f"""
| Number of strings | Number of target languages | Overall Translation ratio |
|:-:|:-:|:-:|
{totalstringcount}|{nb_languages}|{translation_ratio}
""")
    return text


def load_lang_stats(stats):
    """Format statistics of translated languages into a multicolumn table"""
    stats = {k: v for k, v in sorted(stats.items(), key=lambda item: item[1]['percentage'], reverse=True)}

    text = "| Language | Translation ratio (%) |"
    text += "\n|:-:|:-:|\n"

    for lang in stats:
        if lang == 'en':
            continue

        text += f"{stats[lang]['name']} {LANGUAGE_MAP.get(lang)}|"
        text += f"[={stats[lang]['percentage']}% \"{stats[lang]['percentage']}\"]|\n"

    return text


# Store the stats as a table in a rst file
statsfile = path.join(path.dirname(__file__), '..', 'docs/translation-stats.md')
with open(statsfile, 'w') as f:
    f.write(f"""---
hide:
  - navigation
---

<!--
DO NOT EDIT THIS FILE DIRECTLY.
It is generated automatically by transifex_stats.py in the scripts folder.
-->

The translation is available on [Transifex](https://www.transifex.com/quickosm/gui/), no development
knowledge is required.

*Statistics updated: {date.today()}*
{load_overall_stats()}
{load_lang_stats(language_rate)}
""")


with open("QuickOSM/resources/json/i18n.json", 'w', encoding="utf8") as f:
    json.dump(language_rate, f, indent=4)
