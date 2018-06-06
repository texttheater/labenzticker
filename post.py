#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import config
import logging
import MySQLdb
import re
import sys
import tweepy
import urllib2

from BeautifulSoup import BeautifulStoneSoup

wikilink_pattern = re.compile(r'\[\[(?:[^|]+\|)?([^]]+)\]\]')

def strip_tags(html):
    soup = BeautifulStoneSoup(html,
            convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
    return ''.join(soup.findAll(text=True))

def strip_wikilinks(text):
    return wikilink_pattern.sub((lambda m: u'\u2192 %s' % m.group(1)), text)

db = MySQLdb.connect(host=config.host, user=config.user, passwd=config.passwd,
        db=config.db, charset='utf8', use_unicode=True)
cursor = db.cursor()
cursor.execute("""SELECT id, stw, stw_sanitus, UPPER(LEFT(stw_sortoren, 1)) AS bst, gra, ekl
        FROM labenz
        WHERE aufgenommen IS NOT NULL
        AND veroeffentlicht IS NOT NULL
        AND original = 0
        ORDER BY RAND()
        LIMIT 0,1""")
results = cursor.fetchall()
(id, stw, stw_sanitus, bst, gra, ekl) = results[0]
db.close()

auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
api = tweepy.API(auth)

urllen = 23 # this might change, TODO check for this
# tweet = stw + gra + colon + space + ekl + space + url
ekllen = 280 - len(stw) - len(gra) - 2 - 1 - urllen

if ekllen < 0:
    logging.fatal('No characters left for definition of %s' % stw)
    sys.exit(1)

ekl = strip_wikilinks(strip_tags(ekl))

if ekllen < len(ekl):
    ekl = u'%s\u2026' % ekl[:ekllen - 2] # ellipsis counts double towards tweet length

url = 'http://labenz.texttheater.net/%s' % urllib2.quote(stw.encode('UTF-8'))

tweet = '%s%s: %s %s' % (stw, gra, ekl, url)

api.update_status(tweet)
