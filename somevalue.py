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


def testSnak(snak, task):
    if snak['datatype'] != 'wikibase-item':
        return False
    if 'datavalue' not in snak:
        return False
    if snak['datavalue']['value']['id'] != tasks[task]:
        return False
    return True

def move(claim, task):
    mydata = {}
    mydata['claims'] = [claim]
    item = pywikibot.ItemPage(repo, q)
    item.editEntity(mydata, summary=u'move claim [['+tasks[task]+']] -> '+task)


for task in tasks:
    payload = {
        'query': '''SELECT ?item WHERE {{
            ?item ?p ?statement .
            ?statement ?pq wd:'''+tasks[task]+''' .
            ?p ^wikibase:claim [] .
            ?pq ^wikibase:qualifier []
            } UNION {
            ?item ?p wd:'''+tasks[task]+''' .
            ?p ^wikibase:directClaim [] .
            }
        }''',
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
                if testSnak(m['mainsnak'], task):
                    del m['mainsnak']['datavalue']
                    m['mainsnak']['snaktype'] = task
                    move(m, task)
                if 'qualifiers' in m:
                    for qp in m['qualifiers']:
                        for quali in m['qualifiers'][qp]:
                            testSnak(quali, task)
                            if quali['datatype'] == 'wikibase-item' and 'datavalue' in quali:
                                if quali['datavalue']['value']['id'] == tasks[task]:
                                    del quali['datavalue']
                                    quali['snaktype'] = task
                                    move(m, task)
