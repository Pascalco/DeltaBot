#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import re

site = pywikibot.Site('wikidata', 'wikidata')

categories = ['Generic', 'Place', 'Authority control', 'Creative work', 'Transportation', 'Person', 'Natural science', 'Organization', 'Sister projects', 'Sports', 'Lexemes', 'Computing']
text = '<includeonly>{{#switch: {{{1}}}\n'
for category in categories:
    cnt = 0
    page = pywikibot.Page(site, 'Wikidata:Property_proposal/'+category)
    fo = page.get().split('</noinclude>')
    proposals = re.findall('{{Wikidata:Property proposal/(.*?)}}', fo[1])
    if proposals:
        for proposal in proposals:
            page2 = pywikibot.Page(site,'Wikidata:Property proposal/'+proposal)
            if page2.isRedirectPage():
                page2 = page2.getRedirectTarget()
            if not page2.exists():
                continue
            cnt += re.sub(r'(<!([^>]+)>)|\s|\n', '', page2.get()).count('status=|')

    text += '| '+category+' = '+str(cnt)+'\n'
text += '| #default = <strong class="error">invalid parameter <kbd>{{{1}}}</kbd></strong>\n}}</includeonly>'
page = pywikibot.Page(site, 'Wikidata:Property proposal/count')
page.put(text, summary='upd', minor=False)
