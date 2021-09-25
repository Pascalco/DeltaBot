#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
from datetime import datetime
import re

site = pywikibot.Site('wikidata', 'wikidata')


# remove requests from Wikidata:Requests_for_permissions/Bot
def removeRequests(requests):
    page = pywikibot.Page(site, 'Wikidata:Requests for permissions/Bot')
    text = page.get()
    for request in requests:
        text = re.sub(r'{{Wikidata:Requests[\s_]for[\s_]permissions/Bot/'+re.escape(request['name'])+'}}\n?', '', text)
    comment = 'archiving '+str(len(requests))+' requests' if len(requests) != 1 else 'archiving 1 request'
    page.put(text, summary=comment, minor=False)


# load new archive page
def loadNewArchivePage(archive):
    page = pywikibot.Page(site, 'Wikidata:Requests for permissions/RfBot/'+archive)
    if not page.exists():
        newarchive = ("""{{archive|category=Archived requests for permissions}}
                    = Successful requests =

                    = Unsuccessful requests =
                    """)
        page.put(newarchive, summary='Bot: Creating new monthly archive.', minor=False)
    return page.get().replace('_', ' ')


# add requests to archive
def updateArchive(requests):
    archives = {}
    for request in requests:
        if request['archive'] not in archives:
            archives[request['archive']] = {'text': loadNewArchivePage(request['archive']), 'count': 0}
        newText = ''
        for line in archives[request['archive']]['text'].split('\n'):
            newText += line+'\n'
            if (re.match('=\s*successful requests\s*=', line.lower()) and request['status'] == 'success') or (re.match('=\s*unsuccessful requests\s*=', line.lower()) and request['status'] != 'success'):
                newText += '* [[Wikidata:Requests for permissions/Bot/' + request['name'].replace('_', ' ') + ']]\n'
                archives[request['archive']]['count'] += 1
        archives[request['archive']]['text'] = newText.strip()
    for archive in archives:
        page = pywikibot.Page(site, 'Wikidata:Requests for permissions/RfBot/' + archive)
        comment = 'archiving '+str(archives[archive]['count'])+' requests' if archives[archive]['count'] != 1 else 'archiving 1 request'
        page.put(archives[archive]['text'], summary=comment, minor=False)


def main():
    toArchive = []
    page = pywikibot.Page(site, 'Wikidata:Requests for permissions/Bot')
    fo = page.get().split('</noinclude>')
    requests = re.findall('{{Wikidata:Requests[\s_]for[\s_]permissions/Bot/(.*)}}', fo[1])
    for request in requests:
        page2 = pywikibot.Page(site, 'Wikidata:Requests for permissions/Bot/' + request)
        if page2.isRedirectPage():
            page2 = page2.getRedirectTarget()
        if '{{discussion top' in page2.get().lower():
            if '{{approved}}' in page2.get().lower():
                status = 'success'
            else:
                status = 'notdone'
            history = page2.getVersionHistory()
            date = '{0:%B} {0:%Y}'.format(history[0].timestamp)
            data = {
                'name': request,
                'archive': date,
                'status': status
            }
            toArchive.append(data)
    if len(toArchive) > 0:
        updateArchive(toArchive)
        removeRequests(toArchive)


if __name__ == "__main__":
    main()
