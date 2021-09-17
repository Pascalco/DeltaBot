#!/usr/bin/python
# -*- coding: UTF-8 -*-
# licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import requests
import json
import mwparserfromhell as mwparser
import time
import sys
import re

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

template = 'Complex constraint'

blacklist = ['http://www.wikidata.org/entity/Q4115189', 'http://www.wikidata.org/entity/Q13406268', 'http://www.wikidata.org/entity/Q15397819', 'http://www.wikidata.org/entity/Q16943273', 'http://www.wikidata.org/entity/Q17339402']

all = []

maxQTemplate = 4000


def formatQP(val, qTemplateCnt):
    if 'http://www.wikidata.org/entity/' not in val:
        return val, qTemplateCnt
    val = val.replace('http://www.wikidata.org/entity/', '')
    if qTemplateCnt < maxQTemplate:
        qTemplateCnt += 1
        if val[0] == 'Q':
            return '{{{{Q|{}}}}}'.format(val), qTemplateCnt
        elif val[0] == 'P':
            return '{{{{P|{}}}}}'.format(val), qTemplateCnt
        else:
            return val, qTemplateCnt
    else:
        if val[0] == 'Q':
            return '[[{}]]'.format(val), qTemplateCnt
        elif val[0] == 'P':
            return '[[Property:{}]]'.format(val), qTemplateCnt
        else:
            return val, qTemplateCnt


def dictify(t):
    data = {}
    for param in t.params:
        data[str(param.name).strip().lower()] = str(param.value).strip()
    return data


def writeOverview():
    row = u'{{{{TR complex constraint|p={property}\n|label={label}\n|description={description}\n|violations={violations}\n}}}}\n'
    text = u'{{/header|' + time.strftime('%Y-%m-%d') + '}}\n\n'
    for m in all:
        text += row.format(**m)
    text += u'{{/footer}}\n[[Category:Database reports|Complex Constraints]]'
    page = pywikibot.Page(site, 'Wikidata:Database reports/Complex constraints')
    page.put(text, comment='upd', minorEdit=False)


def writeText(onePdata, property):
    text = u'{{Complex constraint violations report|date=' + time.strftime('%Y-%m-%d %H:%M (%Z)') + '}}\n'
    qTemplateCnt = 0
    for m in onePdata:
        text += '\n== '
        text += m['label']
        text += ' ==\n'
        if m['description']:
            text += m['description'] + '\n\n'
        if m['violations'] == 0:
            text += 'no results or query error\n\n'
        else:
            text += 'violations count: ' + str(m['violations']) + '\n\n'
            res = sorted(m['result'], key=lambda x: (int(re.split('(\d+)', x[0])[1])))
            if m['violations'] > 5000:
                res = res[:5000]
            for line in res:
                for i in range(len(line)):
                    var, qTemplateCnt = formatQP(line[i], qTemplateCnt)
                    if i == 0:
                        text += '*'
                    elif i == 1:
                        text += ': '
                    else:
                        text += ', '
                    text += var
                text += '\n'
    page = pywikibot.Page(site, 'Wikidata:Database reports/Complex constraint violations/' + property)
    page.put(text, summary='upd', minorEdit=False)


def proceedOne(sparql):
    result = []
    try:
        url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
        headers = {'user-agent': 'DeltaBot Complex Constraints'}
        payload = {
            'query': sparql,
            'format': 'json'
        }
        r = requests.get(url, params=payload, headers=headers)
        data = r.json()
        for m in data['results']['bindings']:
            if m['item']['value'] in blacklist:
                continue
            line = [m['item']['value']]
            for var in data['head']['vars']:
                if var != 'item':
                    val = m[var]['value'].replace('T00:00:00Z', '')
                    line.append(val)
            result.append(line)
    except:
        pass
    return result


def onePropertyReport(page):
    onePdata = []
    code = mwparser.parse(page.get())
    property = page.title().split(':')[1]
    for t in code.filter_templates():
        if t.name.strip() == template:
            data = dictify(t)
            data['property'] = property
            data['sparql'] = data['sparql'].replace('{{!!}}', '||').replace('{{!}}', '|')
            if not data['label'] or not data['sparql']:
                continue
            if data['label'] == '' or data['sparql'] == '':
                continue
            if not data['description']:
                data['description'] = ''
            data['result'] = proceedOne(data['sparql'])
            data['violations'] = len(data['result'])
            onePdata.append(data)
            all.append(data)
    writeText(onePdata, property)


def main():
    if sys.argv[1] == 'all':
        templatepage = pywikibot.Page(site, 'Template:'+template)
        gen = templatepage.getReferences(onlyTemplateInclusion=True, namespaces=[1, 121], content=True)

        for page in gen:
            try:
                onePropertyReport(page)
            except:
                pass
        writeOverview()
    else:
        if sys.argv[1][0] == 'P':
            page = pywikibot.Page(site, 'Property_talk:'+sys.argv[1])
        else:
            page = pywikibot.Page(site, 'Talk:'+sys.argv[1])
        onePropertyReport(page)


if __name__ == "__main__":
    main()
