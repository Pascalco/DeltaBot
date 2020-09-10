# !/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

from __future__ import unicode_literals
import datetime
import pywikibot
import re
import requests

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

headerPR = '<!-- NEW PROPERTIES DO NOT REMOVE -->'
footerPR = '<!-- END NEW PROPERTIES -->'
headerPP = '<!-- NEW PROPOSALS DO NOT REMOVE -->'
footerPP = '<!-- END NEW PROPOSALS -->'


def getLatestNewsletter():
    cat = pywikibot.Category(site, 'Wikidata status updates')
    ps = list(cat.articles(namespaces=4, sortby='timestamp', reverse=True))
    for p in ps:
        if 'Wikidata:Status updates/2' in p.title() and p.depth == 1:
            return str(p.oldest_revision['timestamp'])


def newProposals(startdate):
    externalIdProps = []
    generalProps = []
    cat = pywikibot.Category(site, 'Open property proposals')
    ps = list(cat.articles(recurse=1, namespaces=4, sortby='timestamp', starttime=startdate))
    for p in ps:
        text = re.sub(r'(<!([^>]+)>)|\s|\n', '', p.get()).lower()
        if text.count('status=|') or text.count('status=ready|') > 0:
            props = externalIdProps if (text.count('datatype=external-id') + text.count('datatype=id')) > 0 else generalProps
            props.append('[[:d:{0}|{1}]]'.format(p.title(), p.title().replace('Wikidata:Property proposal/', '')))
    externalIdText = ', '.join(externalIdProps) if externalIdProps else 'none'
    otherText = ', '.join(generalProps) if generalProps else 'none'

    text = '* New [[d:Special:MyLanguage/Wikidata:Property proposal|property proposals]] to review:\n' + \
           '** General datatypes: ' + otherText + '\n' + \
           '** External identifiers: ' + externalIdText

    return text


def newProperties(startdate):
    payload = {
        'action': 'query',
        'list': 'recentchanges',
        'rctype': 'new',
        'rcnamespace': '120',
        'rclimit': 100,
        'rcend': str(startdate),
        'format': 'json'
    }
    r = requests.get('https://www.wikidata.org/w/api.php', params=payload)
    data = r.json()
    data['query']['recentchanges'].sort(key=lambda m: m['pageid'])

    externalIdProps = []
    generalProps = []
    for m in data['query']['recentchanges']:
        entity = pywikibot.PropertyPage(repo, m['title'].replace('Property:', ''))
        entity.get()
        label = entity.labels['en'] if 'en' in entity.labels else m['title'].replace('Property:', '')
        props = externalIdProps if entity.type == 'external-id' else generalProps
        props.append('[[:d:{0}|{1}]]'.format(m['title'], label))
    externalIdText = ', '.join(externalIdProps) if externalIdProps else 'none'
    otherText = ', '.join(generalProps) if generalProps else 'none'

    text = '* Newest [[d:Special:ListProperties|properties]]:\n' + \
           '** General datatypes: ' + otherText + '\n' + \
           '** External identifiers: ' + externalIdText

    return text


def main():
    latestNewsletter = getLatestNewsletter()
    startdate = latestNewsletter[0:11]+'00:00:00Z'
    text1 = newProperties(startdate)
    text2 = newProposals(startdate)
    page = pywikibot.Page(site, 'Wikidata:Status updates/Next')
    newtext = re.sub(headerPR + '.*' + footerPR, headerPR + '\n' + text1 + '\n' + footerPR, page.get(), flags=re.DOTALL)
    newtext = re.sub(headerPP + '.*' + footerPP, headerPP + '\n' + text2 + '\n' + footerPP, newtext, flags=re.DOTALL)
    page.put(newtext, 'Bot: Updating list of new properties and property proposals')


if __name__ == "__main__":
    main()
