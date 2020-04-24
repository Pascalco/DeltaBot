#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import MySQLdb
import pywikibot
import requests
import json
from datetime import date, timedelta

db = MySQLdb.connect(host="wikidatawiki.labsdb", db="wikidatawiki_p", read_default_file="~/replica.my.cnf")
site = pywikibot.Site('wikidata','wikidata')

blacklist = ['Q4115189','Q13406268','Q15397819','Q16943273','Q17339402'] #sandbox, tour items
blacklist2 = ['Q4167410', 'Q11266439', 'Q4167836'] #disambiguation, template, category items

text = ''
i = 0
img = None
t1 = date.today().strftime('%Y%m%d%H0000')
t2 = (date.today() - timedelta(days=2)).strftime('%Y%m%d%H0000')
cur = db.cursor()
cur.execute('SELECT rc_title, COUNT(*) AS cnt FROM recentchanges WHERE rc_source="mw.edit" AND rc_bot=0 AND rc_namespace=0 AND rc_patrolled<>0 AND rc_timestamp<{} AND rc_timestamp>{} AND rc_old_len<rc_new_len AND rc_title NOT IN (SELECT pl_title FROM pagelinks WHERE pl_from = 26001882 AND pl_namespace = 0) GROUP BY rc_title HAVING COUNT(DISTINCT rc_actor) >= 3 ORDER BY cnt DESC'.format(t1,t2))
for row in cur.fetchall():
    q = row[0].decode()
    if q in blacklist:
        continue
    r = requests.get('https://www.wikidata.org/w/api.php?action=wbgetclaims&entity={}&format=json'.format(q))
    data = r.json()
    if 'error' in data:
        continue
    if 'claims' in data:
        if 'P31' in data['claims']:
            if data['claims']['P31'][0]['mainsnak']['snaktype'] == 'value':
                if data['claims']['P31'][0]['mainsnak']['datavalue']['value']['id'] in blacklist2:
                    continue

    text += '* {{Q|'+q+'}}'

    if not img:
        if 'claims' in data:
            if 'P18' in data['claims']:
                if data['claims']['P18'][0]['mainsnak']['snaktype'] == 'value':
                    img = data['claims']['P18'][0]['mainsnak']['datavalue']['value']
                    text = '<span style="float:right; padding-top:0.5em; padding-left:0.5em;">[[File:{}|100px]]</span>\n{} ({{{{I18n|pictured}}}})'.format(img, text)
    i += 1
    if i == 7:
        break
    text += '\n'
if not img:
    text = '<nowiki></nowiki>\n' + text
text += '<span style="clear:right;"></span>'
page = pywikibot.Page(site, 'Wikidata:Main Page/Popular')
page.put(text, comment='upd', minorEdit=False)
