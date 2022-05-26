#!/usr/bin/env python3

import logging
import re
import sys
import urllib.parse


from bs4 import BeautifulSoup
import mysql.connector
import tweepy


import config


def html2txt(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = ''.join(soup.findAll(text=True))
    text = re.replace(r'\s+', ' ', text)


def strip_wikilinks(text):
    pattern = re.compile(r'\[\[(?:[^]|]+\|)?([^]]+)\]\]')
    return WIKILINK_PATTERN.sub((lambda m: '→ %s' % m.group(1)), text)


def is_lightweight(char):
    o = ord(char)
    ranges = (
        range(0, 4352),
        range(8192, 8206),
        range(8208, 8224),
        range(8242, 8248),
    )
    return any(o in r for r in LIGHTWEIGHT_CHAR_RANGES)


def twlen(chars):
    return sum(1 if is_lightweight(c) else 2 for c in chars)


if __name__ == '__main__':
    # Get random tweet from DB
    db = mysql.connector.connect(host=config.host, user=config.user,
            password=config.passwd, database=config.db)
    cursor = db.cursor()
    cursor.execute("""SELECT id, stw, stw_sanitus,
            UPPER(LEFT(stw_sortoren, 1)) AS bst, gra, ekl
            FROM labenz
            WHERE aufgenommen IS NOT NULL
            AND veroeffentlicht IS NOT NULL
            AND original = 0
            ORDER BY RAND()
            LIMIT 0,1""")
    results = cursor.fetchall()
    (id, stw, stw_sanitus, bst, gra, ekl) = results[0]
    db.close()
    # Connect to Twitter API
    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_token_secret)
    api = tweepy.API(auth)
    # How many characters do we have for the definition?
    urllen = 23 # this might change, TODO check for this
    # tweet = stw + gra + colon + space + ekl + space + url
    ekllen = 280 - twlen(stw) - twlen(gra) - 2 - 1 - urllen
    if ekllen < 0:
        logging.fatal('No characters left for definition of %s' % stw)
        sys.exit(1)
    # Format the definition
    ekl = strip_wikilinks(strip_tags(ekl))
    # Shorten the definition to fit in a tweet
    if twlen(ekl) > ekllen:
        ekllen -= 2 # for … character
        while twlen(ekl) > ekllen:
            ekl = ekl[:-1]
        ekl += '…'
    # Format the tweet
    url = 'https://labenz.neutsch.org/%s' % urllib.parse.quote(stw.encode('UTF-8'))
    tweet = '%s%s: %s %s' % (stw, gra, ekl, url)
    # Send!
    print(tweet, file=sys.stderr)
    api.update_status(tweet)
