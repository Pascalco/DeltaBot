#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from pywikibot.data import api
import re

site = pywikibot.Site('wikidata', 'wikidata')
site.login()
repo = site.data_repository()


def addition_check(q1, q2):
    # only pass if not linked together
    params2 = {
        'action': 'query',
        'titles': q1,
        'prop': 'links',
        'pllimit': 500
    }
    req2 = api.Request(site=site, **params2)
    data2 = req2.submit()
    for m in data2['query']['pages']:
        try:
            for m in data2['query']['pages'][m]['links']:
                if q2 == m['title']:
                    return False
        except:
            pass

    # check if q1 has wikimedia in its description but not q2
    item1 = pywikibot.ItemPage(repo, q1)
    item2 = pywikibot.ItemPage(repo, q2)
    item1.get()
    item2.get()
    if 'en' in item1.descriptions and 'en' in item2.descriptions:
        if 'ikimedia' in item1.descriptions['en'] and 'ikimedia' not in item2.descriptions['en']:
            return False

    return True


def merge(fromId, toId):
    if addition_check(fromId, toId) == False:
        return 0
    fromItem = pywikibot.ItemPage(repo, fromId)
    toItem = pywikibot.ItemPage(repo, toId)
    fromItem.mergeInto(toItem, ignore_conflicts='description')
    if not fromItem.isRedirectPage():
        clearItem(fromId)
        fromItem.set_redirect_target(toItem, force=True, save=True)


def clearItem(fromId):
    # get token
    params = {
        'action': 'query',
        'meta': 'tokens'
    }
    req = api.Request(site=site, **params)
    data = req.submit()
    # clear item
    params2 = {
        'action': 'wbeditentity',
        'id': fromId,
        'clear': 1,
        'data': '{}',
        'bot': 1,
        'summary': 'clearing item to prepare for redirect',
        'token': data['query']['tokens']['csrftoken']
    }
    req2 = api.Request(site=site, **params2)
    data2 = req2.submit()


def check(q1):
    item = pywikibot.ItemPage(repo, q1)
    # ignore redirects and deleted items
    if item.isRedirectPage():
        return 0
    if not item.exists():
        return 0
    # ignore items with sitelinks and more than 3 claims
    dict = item.get()
    if len(dict['sitelinks']) != 0:
        return 0
    if len(dict['claims']) > 3:
        return 0
    # ignore items with more than 10 backlinks
    params2 = {
        'action': 'query',
        'list': 'backlinks',
        'bltitle': q1,
        'blnamespace': 0,
        'bllimit': 11
    }
    req2 = api.Request(site=site, **params2)
    data2 = req2.submit()
    if len(data2['query']['backlinks']) > 10:
        return 0
    # ignore items with link to WD namespace
    params2 = {
        'action': 'query',
        'list': 'backlinks',
        'bltitle': q1,
        'blnamespace': 4,
        'bllimit': 1
    }
    req2 = api.Request(site=site, **params2)
    data2 = req2.submit()
    if len(data2['query']['backlinks']) > 0:
        return 0
    # ignore items in Category:Notability policy exemptions
    cat = pywikibot.Category(site, 'Category:Notability policy exemptions')
    liste = list(cat.articles(recurse=5))
    for m in liste:
        if q1 == m.title()[5:]:
            return 0
    # ignore items where all removed sitelinks are not added to the same new item
    params1 = {
        'action': 'query',
        'prop': 'revisions',
        'titles': q1,
        'rvlimit': 200
    }
    req1 = api.Request(site=site, **params1)
    data1 = req1.submit()
    q2 = False
    for foo in data1['query']['pages']:
        for m in data1['query']['pages'][foo]['revisions']:
            res = re.search(
                'wbsetsitelink-remove\:1\|(.*)wiki \*\/ (.*)', m['comment'])
            if res:
                try:
                    site2 = pywikibot.Site(
                        res.group(1).replace('_', '-'), "wikipedia")
                    page = pywikibot.Page(site2, res.group(2))
                    item2 = pywikibot.ItemPage.fromPage(page)
                    if item2.exists():
                        qTem = item2.getID()
                        if not q2 or q2 == qTem:
                            q2 = qTem
                        else:
                            return 0
                except:
                    return 0
    if q2:
        try:
            merge(q1, q2)
        except:
            pass
        return 1


def main():
    time_file = 'uncompleteMerges_time.dat'
    f1 = open(time_file, 'r')
    oldTime = str(int(f1.read())+1)
    f1.close()
    rccontinue = oldTime+'|0'
    while True:
        params = {
            'action': 'query',
            'list': 'recentchanges',
            'rcprop': 'title|comment|timestamp',
            'rcstart': oldTime,
            'rcdir': 'newer',
            'rctype': 'edit',
            'rcnamespace': 0,
            'rcshow': '!bot',
            'rclimit': 500,
            'rccontinue': rccontinue
        }
        req = api.Request(site=site, **params)
        data = req.submit()
        for m in data['query']['recentchanges']:
            timestamp = m['timestamp']
            if 'comment' not in m:
                continue
            res = re.search(
                'wbsetsitelink-remove\:1\|(.*)wiki \*\/ (.*)', m['comment'])
            if res:
                check(m['title'])
        if 'query-continue' in data:
            rccontinue = data['query-continue']['recentchanges']['rccontinue']
        else:
            break
    f3 = open(time_file, 'w')
    f3.write(re.sub(r'\:|\-|Z|T', '', timestamp))
    f3.close()


if __name__ == "__main__":
    main()
