#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import json
import requests
from datetime import datetime

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

def setRank(q, p):
    r = requests.get('https://wikidata.org/w/api.php?action=wbgetentities&ids='+q+'&format=json')
    data = r.json()
    mydata = {'claims' : []}
    if p not in data['entities'][q]['claims']:
        print('error')
        return 0
    alldates = {}
    for idx in range(len(data['entities'][q]['claims'][p])):
        claim = data['entities'][q]['claims'][p][idx]
        if 'qualifiers' in claim:
            if 'P585' in claim['qualifiers']:
                qualvalues = []
                for qualifier in claim['qualifiers']['P585']:
                    if 'datavalue' not in qualifier:
                        continue #novalue or unknown value
                    if p == 'P3872' and qualifier['datavalue']['value']['precision'] != 9:
                        continue #only consider year precision for P3872
                    qualvalues.append(qualifier['datavalue']['value']['time'])
                if len(qualvalues) > 0:
                    alldates[idx] = max(qualvalues)
    if len(alldates) == 0:
        return 0
    newest_val = max(alldates.values())
    newest = [key for key, value in alldates.items() if value == newest_val]
    if len(newest) != 1:
        return 0 # multiple newest values
    newest = newest[0]
    tdiff = datetime.today() - datetime(int(newest_val[1:5]), 1, 1)
    if tdiff.days > 11*360:
        return 0 #newest value is too old
    if data['entities'][q]['claims'][p][newest]['rank'] != 'normal':
        return 0 #newest value is not set to normal
    for idx in range(len(data['entities'][q]['claims'][p])):
        claim = data['entities'][q]['claims'][p][idx]
        if idx == newest:
            claim['rank'] = 'preferred'
            mydata['claims'].append(claim)
        elif claim['rank'] == 'preferred':
            claim['rank'] = 'normal'
            mydata['claims'].append(claim)

    item = pywikibot.ItemPage(repo, q)
    item.editEntity(mydata, summary='set rank of newest [[Property:'+p+']] to preferred')

for p in ['P1081', 'P1082', 'P1538', 'P1539',  'P1540', 'P3872', 'P6498', 'P6499']:
    payload = {
        'query': """SELECT ?item (count(*) as ?cnt) WHERE {
      ?item wdt:"""+p+""" []
    } group by ?item having(?cnt > 1)
    """,
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    data = r.json()
    for m in data['results']['bindings']:
        try:
            q = m['item']['value'].replace('http://www.wikidata.org/entity/', '')
            setRank(q, p)
        except:
            pass