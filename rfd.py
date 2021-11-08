#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import re

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

page = pywikibot.Page(site, 'Wikidata:Requests for deletions')

cntDone = 0
cntNotDone = 0
force = False

content = re.findall(r'(?:(?<!=)==([^=]+)==(?!=))?([\s\S]+?(?=$|(?<!=)==[^=]+==(?!=)))', page.get())
for i in range(len(content)):
    try:
        content[i] = list(map(str.strip, list(content[i])))
        res = re.search(r'(Q\d+)', content[i][0])
        if res:
            entity = pywikibot.ItemPage(repo, res.group(1))
        else:
            res = re.search(r'(Lexeme:L\d+)', content[i][0])
            if res:
                entity = pywikibot.Page(repo, res.group(1))  # T189321
        if res:
            if any(x in content[i][1] for x in ('{{done', '{{deleted', '{{not done', '{{notdone', '{{not deleted', '{{merged')):
                continue
            if not entity.exists() and not entity.isRedirectPage():
                for m in site.logevents(logtype='delete', page=entity, total=1):
                    content[i][1] += u'\n: {{{{deleted|admin={}}}}} --~~~~'.format(m.user())
                cntDone += 1
            elif entity.isRedirectPage() and entity.getRedirectTarget().exists():
                content[i][1] += (u'\n: {{{{done}}}} Redirect created by [[User:{}]], you can do it ' +
                                  u'[[Special:MyLanguage/Help:Merge|yourself]] next time. --~~~~').format(entity.userName())
                cntDone += 1
            else:
                if '{{on hold' not in content[i][1]:
                    refs = list(entity.backlinks(follow_redirects=False, filter_redirects=False, namespaces=[0, 120], total=12))
                    numberOfRefs = len(refs)
                    if entity in refs:
                        numberOfRefs -= 1
                    if numberOfRefs > 0:
                        force = True
                        content[i][1] += u'\n: {{{{on hold}}}} This item is linked from {}{} other{}. --~~~~'.format(
                            min(numberOfRefs, 10), '+' if numberOfRefs > 10 else '', 's' if numberOfRefs > 1 else '')
                cntNotDone += 1
    except:
        pass

text = ''
for section in content:
    if section[0] != '':
        text += u'== {} ==\n\n'.format(section[0])
    text += section[1]+'\n\n'

if cntDone > 0 or force:
    comment = 'Bot: marking {} requests as done ({} unactioned requests)'.format(cntDone, cntNotDone)
    #page.put(text, summary=comment, minor=False)

print(cntDone, cntNotDone)

statspage = pywikibot.Page(site, 'User:BeneBot*/RfD-stats')
#statspage.put(cntNotDone, summary='Updating stats: '+str(cntNotDone), minor=False)
