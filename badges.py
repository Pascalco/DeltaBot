#!/usr/bin/python
#  -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import requests
import json
import pywikibot
from pywikibot.data import api

site = pywikibot.Site('wikidata', 'wikidata')
site.login()
repo = site.data_repository()
site.get_tokens('edit')

ERROR_THRES = 50

r = requests.get('https://www.wikidata.org/wiki/User:DeltaBot/badges?action=raw')
tasks = r.json()

# remove badges
for t in tasks:
    payload = {
        'categories': t['category'],
        'language': t['language'],
        'project': t['project'],
        'sparql': 'SELECT ?item WHERE { ?article schema:about ?item;wikibase:badge wd:'+t['badge']+';schema:isPartOf <https://'+t['language']+'.'+t['project']+'.org/>}',
        'source_combination': 'sparql not categories',
        'ns[0]': 1,
        'ns[100]': 1,
        'common_wiki': 'wikidata',
        'format': 'json',
        'doit': 'Do it!'
    }
    r = requests.get('https://petscan.wmflabs.org/', params=payload)
    data = r.json()
    if len(data['*'][0]['a']['*']) > ERROR_THRES:
        continue
    for m in data['*'][0]['a']['*']:
        try:
            params = {
                'action': 'wbsetsitelink',
                'id': m['title'],
                'linksite': t['site'],
                'badges': '',
                'token': site.tokens['edit']
            }
            print(m)
            #req = api.Request(site=site, **params)
            #data = req.submit()
        except:
            pass

# add badges
for t in tasks:
    payload = {
        'categories': t['category'],
        'language': t['language'],
        'project': t['project'],
        'sparql': 'SELECT ?item WHERE { ?article schema:about ?item;wikibase:badge wd:'+t['badge']+';schema:isPartOf <https://'+t['language']+'.'+t['project']+'.org/>}',
        'source_combination': 'categories not sparql',
        'ns[0]': 1,
        'ns[100]': 1,
        'common_wiki': 'wikidata',
        'format': 'json',
        'doit': 'Do it!'
    }
    r = requests.get('https://petscan.wmflabs.org/', params=payload)
    data = r.json()
    if len(data['*'][0]['a']['*']) > ERROR_THRES:
        continue
    for m in data['*'][0]['a']['*']:
        try:
            params = {
                'action': 'wbsetsitelink',
                'id': m['title'],
                'linksite': t['site'],
                'badges': t['badge'],
                'token': site.tokens['edit']
            }
            req = api.Request(site=site, **params)
            data = req.submit()
        except:
            pass
