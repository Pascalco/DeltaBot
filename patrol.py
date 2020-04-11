#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from datetime import timedelta, datetime

start = datetime.today() - timedelta(minutes=15)
starttime = start.strftime('%Y%m%d%H%M%S')

site = pywikibot.Site('wikidata', 'wikidata')
gen = site.recentchanges
generator = gen(start=starttime, bot=False, patrolled=True, reverse=True)


#for rev in site.recentchanges(start=starttime, bot=False, patrolled=True, reverse=True):
for rev in generator:
    try:
        if '/* restore' in rev['comment']:
            comment = rev['comment'].split('|')
            page = pywikibot.Page(site, rev['title'])
            for pagerev in page.revisions():
                if pagerev['revid'] > int(comment[2]) and pagerev['revid'] < rev['revid']:
                    p = site.patrol(revid=pagerev['revid'])
                    next(p)
        elif '/* undo' in rev['comment']:
            comment = rev['comment'].split('|')
            p = site.patrol(revid=comment[2])
            next(p)
    except:
        pass
