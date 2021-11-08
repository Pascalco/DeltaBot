#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from pywikibot.data import api
from datetime import datetime, timedelta
import re
import sys

site = pywikibot.Site('wikidata', 'wikidata')
site.login()
repo = site.data_repository()

cat = pywikibot.Category(site, 'Category:Notability policy exemptions')
liste = list(cat.articles(recurse=5))

def merge(fromId,toId):
    fromItem = pywikibot.ItemPage(repo,fromId)
    toItem = pywikibot.ItemPage(repo,toId)
    fromItem.mergeInto(toItem, ignore_conflicts='description')
    clearItem(fromId)
    fromItem.set_redirect_target(toItem, force=True, save=True)

def clearItem(fromId):
    #get token
    params = {
        'action': 'query',
        'meta': 'tokens'
    }
    req = api.Request(site=site, **params)
    data = req.submit()
    #clear item
    params2 = {
        'action': 'wbeditentity',
        'id': fromId,
        'clear': 1,
        'data':'{}',
        'bot': 1,
        'summary': 'clearing item to prepare for redirect',
        'token': data['query']['tokens']['csrftoken']
    }
    req2 = api.Request(site=site,**params2)
    data2 = req2.submit()

def main():
    time_file = 'missingRedirect_time.dat'
    f1 = open(time_file,'r')
    old_time_str = str(int(f1.read())+1)
    f1.close()
    now = datetime.now()
    new_time = now - timedelta(minutes=10)
    new_time_str = new_time.strftime("%Y%m%d%H%M%S")
    rccontinue = old_time_str+'|0'
    while True:
        params = {
            'action': 'query',
            'list': 'recentchanges',
            'rcprop': 'title|comment|timestamp',
            'rcstart': old_time_str,
            'rcend': new_time_str,
            'rcdir': 'newer',
            'rclimit' : 500,
            'rctype': 'edit',
            'rcnamespace':0,
            'rctoponly':1,
            'rccontinue':rccontinue
        }
        req = api.Request(site=site, **params)
        data = req.submit()
        for m in data['query']['recentchanges']:
            timestamp = m['timestamp']
            if 'comment' in m:
                res = re.search('\/\* wbmergeitems-to:0\|\|(Q[0-9]+) \*\/', m['comment'])
                if res:
                    #ignore items in Category:Notability policy exemptions
                    for ll in liste:
                        if m['title'] == ll.title()[5:]:
                            continue
                    try:
                        merge(m['title'],res.group(1))
                    except:
                        pass
        if 'query-continue' in data:
            rccontinue = data['query-continue']['recentchanges']['rccontinue']
        else:
            break
    f1 = open(time_file, 'w')
    f1.write(re.sub(r'\:|\-|Z|T', '', timestamp))
    f1.close()

if __name__ == "__main__":
    main()
