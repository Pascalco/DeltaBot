#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from datetime import datetime
import re

today = datetime.today()

site = pywikibot.Site('wikidata','wikidata')

#remove proposals from category pages
def removeProposals(proposals):
    categories = {}
    for proposal in proposals:       
        if proposal['category'] not in categories:
            page = pywikibot.Page(site,'Wikidata:Property_proposal/'+proposal['category'])
            te = re.sub(r'(?<!_)_(?!_)',' ',page.get())
            categories[proposal['category']] = {'text': te, 'count': 0}         
        categories[proposal['category']]['text'] = re.sub(r'{{Wikidata:Property proposal/'+proposal['name']+'}}\n?','',categories[proposal['category']]['text'])
        categories[proposal['category']]['count'] += 1
    for category in categories:
        page = pywikibot.Page(site,'Wikidata:Property_proposal/'+category)
        comment = 'archiving '+str(categories[category]['count'])+' proposals' if categories[category]['count'] != 1 else 'archiving 1 proposal'
        page.put(categories[category]['text'],comment=comment,minorEdit=False)  

#load new achive subpage
def loadNewArchivePage(archive):
    page = pywikibot.Page(site,'Wikidata:Property proposal/Archive/'+archive)
    if not page.exists():
        newarchive = ('{{archive|category=Property proposal archive}}\n\n'
                    '==Done==\n\n'
                    '<!--{{PPArchive|Property name|Proposer|Start date|Close date/{{subst:#time:Y-m-d}}|Property ID}}-->\n'
                    '{| class="wikitable sortable"\n'
                    '|-\n'
                    '! Property name !! Proposer !! Start date !! Close date !! Property/Note\n'
                    '|}\n\n'
                    '==Not done==\n\n'
                    '<!--{{PPArchive|Property name|Proposer|Start date|Close date/{{subst:#time:Y-m-d}}|Reason (optional)}}-->\n'
                    '{| class="wikitable sortable"\n'
                    '|-\n'
                    '! Property name !! Proposer !! Start date !! Close date !! Reason\n'
                    '|}')
        page.put(newarchive,comment='new archive',minorEdit=False)
    return page.get().replace('_',' ')

#add proposals to archive    
def updateArchive(proposals):
    proposals.sort(key=lambda x:x['closedate'])
    archives = {}
    for proposal in proposals:
        if proposal['archive'] not in archives:
            archives[proposal['archive']] = {'text': loadNewArchivePage(proposal['archive']), 'count': 0}
        if proposal['newname'] not in archives[proposal['archive']]['text']:
            newText = ''
            look = False
            for line in archives[proposal['archive']]['text'].split('\n'):
                if (re.match('==\s*done\s*==',line.lower()) and proposal['note'].isdigit()) or (re.match('==\s*not done\s*==',line.lower()) and not proposal['note'].isdigit()):
                    look = True
                if line.strip() == '|}' and look:
                    newText += u'{{{{PPArchive|{newname}|{proposer}|{startdate}|{closedate}|{note}}}}}\n'.format(**proposal)
                    archives[proposal['archive']]['count'] += 1
                    look = False
                newText += line+'\n'
            archives[proposal['archive']]['text'] = newText.strip()
    for archive in archives:
        page = pywikibot.Page(site,'Wikidata:Property_proposal/Archive/'+archive)
        comment = 'archiving '+str(archives[archive]['count'])+' proposals' if archives[archive]['count'] != 1 else 'archiving 1 proposal'
        page.put(archives[archive]['text'],comment=comment,minorEdit=False)    

def main():
    toArchive = []
    categories = ['Generic','Event','Place','Economics','Authority control','Creative work','Transportation','Person','Term','Natural science','Organization','Space','Sister projects','Property metadata']
    for category in categories:
        page = pywikibot.Page(site,'Wikidata:Property_proposal/'+category)
        fo = page.get().split('</noinclude>')
        proposals = re.findall('{{Wikidata:Property proposal/(.*)}}',fo[1].replace('_',' '))
        for proposal in proposals:
            page2 = pywikibot.Page(site,'Wikidata:Property proposal/'+proposal)
            if page2.isRedirectPage():
                page2 = page2.getRedirectTarget()
                proposal = page2.title()[27:]
            pptext = re.sub(r'(<!([^>]+)>)|\n','',page2.get())
            if pptext.count('{{Property proposal') > 1: #ToDo: handle pages with multiple proposal
                continue
            res = re.search('\|\s*status\s*=\s*([^\|\}]+)',pptext)
            if res:
                status = res.group(1).strip()
                if status.isdigit() or status.lower() == 'not done' or status.lower() == 'withdrawn':
                    status = status if status != 'not done' else ''
                    history = page2.getVersionHistory()
                    if (today - history[0].timestamp).days >= 3:
                        month = str(history[0].timestamp.month) if history[0].timestamp.month > 9 else '0'+str(history[0].timestamp.month)
                        data = {
                            'name': proposal.replace('_',' '),
                            'newname': proposal,
                            'category': category,
                            'proposer': history[-1].user,
                            'startdate': history[-1].timestamp.date().isoformat(),
                            'closedate': history[0].timestamp.date().isoformat(),
                            'note': status,
                            'archive': str(history[0].timestamp.year)+'/'+month
                        }
                        toArchive.append(data)
    if len(toArchive) > 0:
        updateArchive(toArchive)
        removeProposals(toArchive)

if __name__ == "__main__":
    main()
