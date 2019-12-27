#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from pywikibot.data import api
import re

site = pywikibot.Site('wikidata', 'wikidata')
site.login()
repo = site.data_repository()


def redirect(fromId, toId):
    # get token
    params = {
        'action': 'query',
        'meta': 'tokens'
    }
    req = api.Request(site=site, **params)
    data = req.submit()
    # create redirect
    params3 = {
        'action': 'wbcreateredirect',
        'from': fromId,
        'to': toId,
        'bot': 1,
        'token': data['query']['tokens']['csrftoken']
    }
    req3 = api.Request(site=site, **params3)
    data3 = req3.submit()


def main():
    params = {
        'action': 'query',
        'list': 'querypage',
        'qppage': 'DoubleRedirects',
        'qplimit': 5000
    }
    req = api.Request(site=site, **params)
    data = req.submit()
    for m in data['query']['querypage']['results']:
        try:
            if m['ns'] == 0:
                item1 = pywikibot.ItemPage(repo, m['title'])
                item2 = item1.getRedirectTarget().getRedirectTarget().getID()
                redirect(m['title'], item2)
        except:
            pass

if __name__ == "__main__":
    main()
