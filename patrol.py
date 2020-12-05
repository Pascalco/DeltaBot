#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from datetime import timedelta, datetime

autopatrol = ['Q4115189', 'Q13406268', 'Q15397819', 'Q16943273', 'Q17339402', 'Q17566023', 'Q17578745', 'Q85408509', 'Q85408938', 'Q85409163', 'Q85409310', 'Q85409446', 'Q85409596']

start = datetime.utcnow() - timedelta(minutes=15)
starttime = start.strftime('%Y%m%d%H%M%S')

site = pywikibot.Site('wikidata', 'wikidata')
gen = site.recentchanges

generator = gen(start=starttime, bot=False, patrolled=True, reverse=True)
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


generator = gen(start=starttime, bot=False, patrolled=False, reverse=True)
for rev in generator:
    try:
        if rev['title'] in autopatrol:
            p = site.patrol(revid=rev['revid'])
            next(p)
    except:
        pass
