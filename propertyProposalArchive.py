#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from datetime import datetime
import re

today = datetime.today()

site = pywikibot.Site('wikidata', 'wikidata')


# remove proposals from category pages
def removeProposals(proposals):
    categories = {}
    for proposal in proposals:
        if proposal['category'] not in categories:
            page = pywikibot.Page(site, 'Wikidata:Property_proposal/'+proposal['category'])
            te = re.sub(r'(?<!_)_(?!_)', ' ', page.get())
            categories[proposal['category']] = {'text': te, 'count': 0}
        categories[proposal['category']]['text'] = re.sub(r'{{Wikidata:Property proposal/'+re.escape(proposal['name'])+'}}\n?', '', categories[proposal['category']]['text'], flags=re.IGNORECASE)
        categories[proposal['category']]['count'] += 1
    for category in categories:
        page = pywikibot.Page(site, 'Wikidata:Property_proposal/'+category)
        comment = 'archiving '+str(categories[category]['count'])+' proposals' if categories[category]['count'] != 1 else 'archiving 1 proposal'
        page.put(categories[category]['text'], summary=comment, minor=False)


# load new archive subpage
def loadNewArchivePage(archive):
    page = pywikibot.Page(site, 'Wikidata:Property proposal/Archive/'+archive)
    if not page.exists():
        newarchive = ('{{archive|category=Property proposal archive}}\n\n'
                    '==Done==\n\n'
                    '{| class="wikitable sortable"\n'
                    '|-\n'
                    '! Property name !! Proposer !! Start date !! Close date !! Property !! Label !! Description !! Uses\n'
                    '|}\n\n'
                    '==Not done==\n\n'
                    '{| class="wikitable sortable"\n'
                    '|-\n'
                    '! Property name !! Proposer !! Start date !! Close date !! Reason\n'
                    '|}')
        page.put(newarchive, summary='new archive', minor=False)
    return page.get().replace('_', ' ')


# add proposals to archive
def updateArchive(proposals):
    proposals.sort(key=lambda x: x['closedate'])
    archives = {}
    for proposal in proposals:
        if proposal['archive'] not in archives:
            archives[proposal['archive']] = {'text': loadNewArchivePage(proposal['archive']), 'count': 0}
        if proposal['newname'] not in archives[proposal['archive']]['text']:
            newText = ''
            look = False
            for line in archives[proposal['archive']]['text'].split('\n'):
                if (re.match('==\s*done\s*==', line.lower()) and (proposal['note'] == 'done' or proposal['note'].isdigit())) or (re.match('==\s*not done\s*==', line.lower()) and not (proposal['note'] == 'not done' or proposal['note'].isdigit())):
                    look = True
                if line.strip() == '|}' and look:
                    newText += u'{{{{PPArchive|{newname}|{proposer}|{startdate}|{closedate}|{note}}}}}\n'.format(**proposal)
                    archives[proposal['archive']]['count'] += 1
                    look = False
                newText += line+'\n'
            archives[proposal['archive']]['text'] = newText.strip()
    for archive in archives:
        page = pywikibot.Page(site, 'Wikidata:Property_proposal/Archive/'+archive)
        comment = 'archiving '+str(archives[archive]['count'])+' proposals' if archives[archive]['count'] != 1 else 'archiving 1 proposal'
        page.put(archives[archive]['text'], summary=comment, minor=False)


def allClosed(stati):
    for status in stati:
        if not status:
            return False
        if not status.isdigit() and status.lower() != 'done' and status.lower() != 'not done' and status.lower() != 'withdrawn' and status.lower()[0] != 'p' and not status[1:].isdigit():
            return False
    return True


def main():
    toArchive = []
    categories = ['Generic', 'Place', 'Authority control', 'Creative work', 'Transportation', 'Person', 'Natural science', 'Organization', 'Sister projects', 'Sports', 'Lexemes', 'Commons']
    for category in categories:
        page = pywikibot.Page(site, 'Wikidata:Property_proposal/'+category)
        fo = page.get().split('</noinclude>')
        proposals = re.findall('{{Wikidata:Property proposal/(.*?)}}', fo[1].replace('_', ' '), re.IGNORECASE)
        for proposal in proposals:
            try:
                page2 = pywikibot.Page(site, 'Wikidata:Property proposal/'+proposal)
                if page2.isRedirectPage():
                    page2 = page2.getRedirectTarget()
                    newname = page2.title()[27:]
                elif not page2.exists():
                    continue
                else:
                    newname = proposal
                pptext = re.sub(r'(<!([^>]+)>)|\n', '', page2.get())
                stati = re.findall('\|\s*status\s*=\s*([^\|\}]+)', pptext)
                stati = list(map(str.strip, stati))
                if not allClosed(stati):
                    continue
                for status in stati:
                    if status.lower() == 'not done':
                        status = ''
                    elif status.lower()[0] == 'p' and status[1:].isdigit():
                        status = status[1:]
                    history = list(page2.revisions())
                    if (today - history[0].timestamp).days >= 1:
                        month = '{:02d}'.format(history[0].timestamp.month)
                        data = {
                            'name': proposal.replace('_', ' '),
                            'newname': newname,
                            'category': category,
                            'proposer': history[-1].user,
                            'startdate': history[-1].timestamp.date().isoformat(),
                            'closedate': history[0].timestamp.date().isoformat(),
                            'note': status,
                            'archive': str(history[0].timestamp.year)+'/'+month
                        }
                        toArchive.append(data)
            except Exception as e:
                print(proposal)
                print(type(e))
                print(e)
                pass
    if len(toArchive) > 0:
        updateArchive(toArchive)
        removeProposals(toArchive)

if __name__ == "__main__":
    main()
