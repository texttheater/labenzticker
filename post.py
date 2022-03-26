#!/usr/bin/env python3

import config
import logging
import mysql.connector
import re
import sys
import tweepy
import urllib.parse

from bs4 import BeautifulSoup

wikilink_pattern = re.compile(r'\[\[(?:[^]|]+\|)?([^]]+)\]\]')

def strip_tags(html):
    soup = BeautifulSoup(html)
    return ''.join(soup.findAll(text=True))

def strip_wikilinks(text):
    return wikilink_pattern.sub((lambda m: '\u2192 %s' % m.group(1)), text)

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

client = tweepy.Client(
    #bearer_token=config.bearer_token,
    consumer_key=config.consumer_key,
    consumer_secret=config.consumer_secret,
    access_token=config.access_token,
    access_token_secret=config.access_token_secret,
)

urllen = 23 # this might change, TODO check for this
# tweet = stw + gra + colon + space + ekl + space + url
ekllen = 280 - len(stw) - len(gra) - 2 - 1 - urllen

if ekllen < 0:
    logging.fatal('No characters left for definition of %s' % stw)
    sys.exit(1)

ekl = strip_wikilinks(strip_tags(ekl))

if ekllen < len(ekl):
    ekl = '%s\u2026' % ekl[:ekllen - 2] # ellipsis counts double towards tweet length

url = 'https://labenz.neutsch.org/%s' % urllib.parse.quote(stw.encode('UTF-8'))

tweet = '%s%s: %s %s' % (stw, gra, ekl, url)

print(tweet, file=sys.stderr)

client.create_tweet(tweet)
