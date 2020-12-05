#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import requests
import json

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

qvalue = 'Q53569537'

whitelist = ['Q19798648']

payload = {
    'query': 'SELECT ?item WHERE { ?item ?p wd:Q53569537 . ?p ^wikibase:directClaim [] . } ',
    'format': 'json'
}
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
                if m['mainsnak']['datavalue']['value']['id'] == qvalue:
                    del m['mainsnak']['datavalue']
                    m['mainsnak']['snaktype'] = 'somevalue'
                    mydata = {}
                    mydata['claims'] = [m]
                    item = pywikibot.ItemPage(repo, q)
                    item.editEntity(mydata, summary=u'move claim [['+qvalue+']] -> somevalue')
