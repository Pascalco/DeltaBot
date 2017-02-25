#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import re

site = pywikibot.Site('wikidata','wikidata')
repo = site.data_repository()

page = pywikibot.Page(site,'Wikidata:Requests for deletions')

cntDone = 0
cntNotDone = 0
force = False

content = re.findall(r'(?:(?<!=)==([^=]+)==(?!=))?([\s\S]+?(?=$|(?<!=)==[^=]+==(?!=)))', page.get())
for i in range(0,len(content)):
    content[i] = map(unicode.strip,list(content[i]))
    res = re.search(r'(Q\d+)',content[i][0])
    if res:
        if any(x in content[i][1] for x in ('{{done', '{{deleted', '{{not done', '{{not deleted', '{{merged')):
            continue
        item = pywikibot.ItemPage(repo, res.group(1))
        if item.isRedirectPage():
            content[i][1] += (u'\n: {{{{done}}}} Redirect created by [[User:{}|]], you can do it ' +
                              u'[[Special:MyLanguage/Help:Merge|yourself]] next time. --~~~~').format(item.userName())
            cntDone += 1
        elif not item.exists():
            for m in site.logevents(logtype='delete', page=item, total=1):
                content[i][1] += u'\n: {{{{deleted|admin={}}}}} --~~~~'.format(m.user())
            cntDone += 1
        else:
            if '{{on hold' not in content[i][1]:
                refs = len(list(item.getReferences(follow_redirects=False, withTemplateInclusion=False,
                                                   namespaces=[0, 120], total=11)))
                if refs > 0:
                    force = True
                    content[i][1] += u'\n: {{{{on hold}}}} This item is linked from {}{} other{}. --~~~~'.format(
                        min(refs, 10), '+' if refs > 10 else '', 's' if refs > 1 else '')
            cntNotDone += 1

text = ''
for section in content:
    if section[0] != '':
        text += u'== {} ==\n\n'.format(section[0])
    text += section[1]+'\n\n'

if cntDone > 0 or force:
    comment = 'Bot: marking {} requests as done ({} unactioned requests)'.format(cntDone,cntNotDone)
    page.put(text,comment=comment,minorEdit=False)

statspage = pywikibot.Page(site,'User:BeneBot*/RfD-stats')
statspage.put(cntNotDone,comment='Updating stats: '+str(cntNotDone),minorEdit=False)
