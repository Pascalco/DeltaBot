#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import requests
import json

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

whitelist = ['Q108474139', 'Q53569537']

tasks = {'somevalue': 'Q53569537', 'novalue': 'Q108474139'}

for task in tasks:
    payload = {
        'query': 'SELECT ?item WHERE { ?item ?p wd:'+tasks[task]+' . ?p ^wikibase:directClaim [] . } ',
        'format': 'json'
    }
    print(payload)
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    data = r.json()
    for m in data['results']['bindings']:
        q = m['item']['value'].replace('http://www.wikidata.org/entity/', '')
        if q in whitelist:
            continue
        r = requests.get('https://wikidata.org/w/api.php?action=wbgetentities&ids={}&format=json'.format(q))
        data = r.json()
        if 'entities' not in data:
            continue
        for p in data['entities'][q]['claims']:
            for m in data['entities'][q]['claims'][p]:
                if not 'datavalue' in m['mainsnak']:
                    continue
                if m['mainsnak']['datatype'] == 'wikibase-item':
                    if m['mainsnak']['datavalue']['value']['id'] == tasks[task]:
                        del m['mainsnak']['datavalue']
                        m['mainsnak']['snaktype'] = task
                        mydata = {}
                        mydata['claims'] = [m]
                        item = pywikibot.ItemPage(repo, q)
                        item.editEntity(mydata, summary=u'move claim [['+tasks[task]+']] -> '+task)
