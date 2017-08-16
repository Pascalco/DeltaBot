#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import re

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

db = MySQLdb.connect(host='wikidatawiki.labsdb', db='wikidatawiki_p', read_default_file='~/replica.my.cnf')

cur = db.cursor()
cur.execute('SELECT rc_title, rc_comment FROM recentchanges WHERE rc_namespace=0 AND HEX(rc_comment) LIKE "%E2808F";')

for row in cur.fetchall():
    try:
        res = re.search('\[\[Property:(P\d+)\]\]', row[1])
        if not res:
            continue
        p = res.group(1)
        item = pywikibot.ItemPage(repo, row[0])
        item.get()
        if p in item.claims:
            for claim in item.claims[p]:
                if claim.type in ['string', 'url', 'external-id']:
                    value = claim.getTarget()
                    if u'\u200f' in value:
                        newvalue = value.replace(u'\u200f', '').strip()
                        claim.changeTarget(newvalue)
    except:
        pass
