#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from pywikibot.data import api
import re

site = pywikibot.Site('wikidata','wikidata')

categories = ['Generic','Event','Place','Economics','Authority control','Creative work','Transportation','Person','Term','Natural science','Organization','Space','Sister projects','Property metadata']
text = '<includeonly>{{#switch: {{{1}}}\n'
for category in categories:
    cnt = 0
    page = pywikibot.Page(site,'Wikidata:Property_proposal/'+category)
    fo = page.get().split('</noinclude>')
    proposals = re.findall('{{Wikidata:Property proposal/(.*)}}',fo[1])
    if proposals:
        for proposal in proposals:
            page2 = pywikibot.Page(site,'Wikidata:Property proposal/'+proposal)
            if page2.isRedirectPage():
                params = {
                    'action': 'query',
                    'redirects': True,
                    'titles': 'Wikidata:Property proposal/'+proposal
                }
                req = api.Request(site=site,**params)
                data = req.submit()
                redirects = dict((x['from'], x['to'])
                                 for x in data['query']['redirects'])
                page2 = pywikibot.Page(site,data['query']['redirects'][0]['to'])
            cnt += re.sub(r'(<!([^>]+)>)|\s|\n','',page2.get()).count('status=|')   

    text += '| '+category+' = '+str(cnt)+'\n'
text += '| #default = <strong class="error">invalid parameter <tt>{{{1}}}</strong>\n}}</includeonly>'
page = pywikibot.Page(site,'Wikidata:Property proposal/count')
page.put(text.decode('UTF-8'),comment='upd',minorEdit=False)