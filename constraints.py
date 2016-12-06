#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.
#
# See <http://creativecommons.org/publicdomain/zero/1.0/> for a copy of the
# CC0 Public Domain Dedication.

from __future__ import unicode_literals
import requests
import json
import re
import time
import mwparserfromhell
import pywikibot
from pywikibot.pagegenerators import *

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

types = ['Constraint:Type', 'Constraint:Value type', 'Constraint:Symmatric', 'Constraint:Inverse', 'Constraint:Unique value', 'Constraint:Single value', 'Constraint:Multi value', 'Constraint:Item', 'Constraint:Target required claim', 'Constraint:Units', 'Constraint:Range', 'Constraint:Qualifiers', 'Constraint:Value only', 'Constraint:Qualifier', 'Constraint:Source only', 'Constraint:Format', 'Constraint:One of']
header = '{{{{Constraint violations report|date={}|item count={}}}}}\n'


def logwrite(text):
    f1 = open('logs/constraintslog.dat', 'a')
    f1.write(text)
    f1.close()


def requestquery(query, l=0):
    limit = 'LIMIT '+ str(l) if l > 0 else ''
    payload = {
            'query': '#User:DeltaBot - Constraint violation reports\n' + query + limit,
            'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql', params=payload)
    return r.json(), l


def oneConstraint(p, datatype, template):
    # make list of exceptions
    if template.has('exceptions'):
        exceptions = template.get('exceptions').value.strip().replace('[[', '').replace(']]', '').split(',')
        exceptions = map(unicode.strip, exceptions)
    else:
        exceptions = []

    # write query
    if template.name == 'Constraint:Type':
        relation = 'P279' if template.get('relation').value == 'subclass' else 'P31'
        list = template.get('class').value.split(',') if template.has('class') else template.get('classes').value.split(',')
        list = map(unicode.strip, list)
        classes = 'wd:' + ', wd:'.join(list)
        query = 'SELECT DISTINCT ?item WHERE{{ ?item wdt:{p} [] . MINUS {{ ?item wdt:{relation}/wdt:P279* ?class . FILTER(?class IN ({classes})) }} }} ORDER BY ?item'.format(p=p, relation=relation, classes=classes)
        title = '<span id="Type {}"></span>\n== "Type {{{{Q|{}}}}}" violations =='.format(', '.join(list), '}}, {{Q|'.join(list))

    elif template.name == 'Constraint:Value type':
        relation = 'P279' if template.get('relation').value == 'subclass' else 'P31'
        list = template.get('class').value.split(',') if template.has('class') else template.get('classes').value.split(',')
        list = map(unicode.strip, list)
        classes = 'wd:' + ', wd:'.join(list)
        query = 'SELECT DISTINCT ?item WHERE{{ ?item wdt:{p} ?value . MINUS {{ ?value wdt:{relation}/wdt:P279* ?class . FILTER(?class IN ({classes})) }} }} ORDER BY ?item'.format(p=p, relation=relation, classes=classes)
        title = '<span id="Value type {}"></span>\n== "Value type {{{{Q|{}}}}}" violations =='.format(','.join(list), '}}, {{Q|'.join(list))

    elif template.name == 'Constraint:Symmetric':
        query = 'SELECT DISTINCT ?item { ?item wdt:{p} ?value . MINUS {{ ?value wdt:{p} ?item . }} }} ORDER BY ?item'.format(p=p)
        title = '<span id="Symmetric"></span>\n== "Symmetric" violations =='

    elif template.name == 'Constraint:Inverse':
        property = template.get('property').value
        query = 'SELECT DISTINCT ?item WHERE {{ ?inverse wdt:{p} ?item FILTER NOT EXISTS {{ ?item wdt:{property} ?inverse }} }} ORDER BY ?item'.format(p=p, property=property)
        title = '<span id="Inverse"></span>\n== "Inverse" violations =='

    elif template.name == 'Constraint:Unique value':
        query = 'SELECT DISTINCT ?item (COUNT(?item1) AS ?count)(GROUP_CONCAT(?item1;separator=",") AS ?items) WHERE {{ ?item1 wdt:{p} ?item }} GROUP BY ?item HAVING(?count > 1) ORDER BY ?item1'.format(p=p)
        title = '<span id="Unique value"></span>\n== "Unique value" violations =='
        variables = ['items']

    elif template.name == 'Constraint:Single value':
        query = 'SELECT DISTINCT ?item (COUNT(?value) AS ?count)(GROUP_CONCAT(?value;separator=", ") AS ?values) WHERE {{ ?item wdt:{p} ?value }} GROUP BY ?item HAVING(?count > 1) ORDER BY ?item'.format(p=p)
        title = '<span id="Single value"></span>\n== "Single value" violations =='
        variables = ['values']

    elif template.name == 'Constraint:Multi values':
        query = 'SELECT DISTINCT ?item (COUNT(?value) AS ?count) { ?item wdt:{p} ?value .}} GROUP BY ?item HAVING (?count=1) ORDER BY ?item'.format(p=p)
        title = '<span id="Multi value"></span>\n== "Multi value" violations =='

    elif template.name == 'Constraint:Item':
        property = template.get('property').value
        if template.has('item') or template.has('items'):
            list = template.get('item').value.split(',') if template.has('item') else template.get('items').value.split(',')
            list = map(unicode.strip, list)
            items = 'wd:' + ', wd:'.join(list)
            query = 'SELECT DISTINCT ?item WHERE {{ ?item wdt:{p} [] . MINUS {{ ?item wdt:{property} ?values . FILTER (?values IN ({items})) }} }}'.format(p=p, property=property, items=items)
        else:
            query = 'SELECT DISTINCT ?item WHERE {{ ?item wdt:{p} [] . MINUS {{ ?item wdt:{property} [] }} }}'.format(p=p, property=property)
        title = '<span id="Item {0}"></span>\n== "Item {{{{P|{0}}}}}" violations =='.format(property)

    elif template.name == 'Constraint:Target required claim':
        property = template.get('property').value
        if template.has('item') or template.has('items'):
            list = template.get('item').value.split(',') if template.has('item') else template.get('items').value.split(',')
            list = map(unicode.strip, list)
            items = 'wd:' + ', wd:'.join(list)
            query = 'SELECT DISTINCT ?item WHERE {{ ?item wdt:{p} ?target . MINUS {{ ?target wdt:{property} ?values . FILTER (?values IN ({items})) }} }}'.format(p=p, property=property, items=items)
        else:
            query = 'SELECT DISTINCT ?item WHERE {{ ?item wdt:{p} ?target . MINUS {{ ?target wdt:{property} [] }} }}'.format(p=p, property=property)
        title = '<span id="Target required claim {0}"></span>\n== "Target required claim {{{{P|{0}}}}}" violations =='.format(property)

    elif template.name == 'Constraint:Units':
        list = template.get('list').value.split(',')
        list = map(unicode.strip, list)
        units = 'wd:' + ', wd:'.join(list)
        units = units.replace('none', 'Q199')
        units = units.replace('novalue', 'Q199')
        query = 'SELECT DISTINCT ?item ?unit WHERE {{ ?item p:{p}/psv:{p}/wikibase:quantityUnit ?unit FILTER (?unit NOT IN ({units})) }} ORDER BY ?item'.format(p=p, units=units)
        title = '<span id="Units"></span>\n== "Units" violations =='
        variables = ['unit']

    elif template.name == 'Constraint:Range':
        min = template.get('min').value
        max = template.get('max').value
        if datatype == 'time':
            if max == 'now':
                max = time.strftime('%Y')
            query = 'SELECT DISTINCT ?item ?value WHERE {{ ?item wdt:{p} ?value FILTER (year(?value) < {min} || year(?value) > {max}) }} ORDER BY ?item'.format(p=p, min=min, max=max)
        else:
            query = 'SELECT DISTINCT ?item ?value WHERE {{ ?item wdt:{p} ?value FILTER (?value < {min} || ?value > {max}) }} ORDER BY ?item'.format(p=p, min=min, max=max)
        title = '<span id="Range"></span>\n== "Range" violations =='
        variables = ['value']

    elif template.name == 'Constraint:Qualifiers':
        list = template.get('list').value.split(',')
        list = map(unicode.strip, list)
        if template.has('required'):
            qualifiers = 'pq:' + ' []; pq:'.join(list)
            query = 'SELECT DISTINCT ?item WHERE {{ ?item p:{p} ?statement . MINUS {{ ?statement {qualifiers} [] }} }} ORDER BY ?item'.format(p=p, qualifiers=qualifiers)
        else:
            qualifiers = 'wd:' + ', wd:'.join(list)
            query = 'SELECT DISTINCT ?item WHERE {{ hint:Query hint:optimizer "None" . ?item p:{p} ?statement . ?statement ?pq_qual ?pq_obj . ?qual wikibase:qualifier ?pq_qual . FILTER (?qual NOT IN ({qualifiers})) }} ORDER BY ?item'.format(p=p, qualifiers=qualifiers)
        title = '<span id="Qualifiers"></span>\n== "Qualifiers" violations =='

    elif template.name == 'Constraint:Value only':
        query = 'SELECT DISTINCT ?item WHERE {{ {{ ?statement0 pq:{p} ?value . ?item ?p0 ?statement0 . ?prop wikibase:claim ?p0 . FILTER(?prop != wd:P1855 && ?prop != wd:P2271) }} UNION {{ ?ref pr:{p} ?value . ?statement1 prov:wasDerivedFrom ?ref . ?item ?p1 ?statement1 }} }} ORDER BY ?item'.format(p=p)
        title = '<span id="Value only"></span>\n== "Value only" violations =='

    elif template.name == 'Constraint:Qualifier':
        query = 'SELECT DISTINCT ?item WHERE {{ {{ ?item wdt:{p} ?value . }} UNION {{ ?ref pr:{p} ?value . ?statement1 prov:wasDerivedFrom ?ref . ?item ?p1 ?statement1  }} }} ORDER BY ?item'.format(p=p)
        title = '<span id="Qualifier"></span>\n== "Qualifier" violations =='

    elif template.name == 'Constraint:Source only':
        query = 'SELECT DISTINCT ?item {{ {{ ?item wdt:{p} ?value . }} UNION { ?statement1 pq:{p} ?value . ?item ?p1 ?statement1 }} }} ORDER BY ?item'.format(p=p)
        title = '<span id="Source only"></span>\n== "Source only" violations =='

    elif template.name == 'Constraint:Format':
        pattern = template.get('pattern').value.strip().replace('<nowiki>', '').replace('</nowiki>', '').replace('\\', '\\\\').replace('"', '\\"')
        if pattern[0] == '^':
            pattern = pattern[1:]
        if pattern[-1] == '$':
            pattern = pattern[:-1]
        if datatype == 'commonsMedia':
            pattern = pattern.replace(' ', '%20')
            pattern = 'http://commons.wikimedia.org/wiki/Special:FilePath/' + pattern
        query = 'SELECT DISTINCT ?item ?value WHERE {{ {{ ?item wdt:{p} ?value }} UNION {{ ?statement1 pq:{p} ?value . ?item ?p1 ?statement1 . }} UNION {{ ?ref pr:{p} ?value . ?statement2 prov:wasDerivedFrom ?ref . ?item ?p2 ?statement2 . }} .  FILTER( REGEX(STR(?value), "^{pattern}$") = false ) }} ORDER BY ?item'.format(p=p, pattern=pattern)
        title = '<span id="Format"></span>\n== "Format" violations =='
        variables = ['value']

    elif template.name == 'Constraint:One of':
        list = template.get('values').value.split(',')
        list = map(unicode.strip, list)
        if datatype == 'wikibase-item':
            values = 'wd:' + ', wd:'.join(list)
        else:
            values = ','.join(list)
        query = 'SELECT DISTINCT ?item ?value WHERE {{ ?item wdt:{p} ?value . FILTER (?value NOT IN ({values})) }} ORDER BY ?item'.format(p=p, values=values)
        title = '<span id="One of"></span>\n== "One of" violations =='
        variables = ['value']

    # execute query, if necessary limit number of results
    try:
        data, limit = requestquery(query, 0)
    except:
        try:
            data, limit = requestquery(query, 5000)
        except:
            logwrite('error with '+p+' : '+str(template.name) + '\n' + query + '\n')
            return ''

    violations = []
    cntExceptions = 0
    for m in data['results']['bindings']:
        qid = m['item']['value'].replace('http://www.wikidata.org/entity/', '')
        link = 1
        if template.name == 'Constraint:Unique value':
            if datatype != 'wikibase-item':
                link = 0
            qid = qid.replace('http://commons.wikimedia.org/wiki/Special:FilePath/', '')
            qidlist = m['items']['value'].replace('http://www.wikidata.org/entity/', '').split(',')
        else:
            qidlist = [qid]
        if len(set.intersection(*[set(qidlist), set(exceptions)])) == 0:  # not in exceptions
            if link == 1:
                if qid[0] == 'P':
                    qid = 'Property:' + qid + '|' + qid
                line = '*[[{}]]:'.format(qid)
            else:
                line = '*{}:'.format(qid)
            if 'variables' in locals():
                for n in variables:
                    if 'http://www.wikidata.org/entity/' in m[n]['value']:
                        tt = m[n]['value'].replace('http://www.wikidata.org/entity/', '').split(',')
                        line += ' [[' + ']], [['.join(tt) + ']],'
                    else:
                        line += ' '+m[n]['value'].replace('http://commons.wikimedia.org/wiki/Special:FilePath/', '') + ','
            violations.append(line[:-1])
        else:
            cntExceptions += 1

    violationscount = len(violations) if limit == 0 else 'more than '+str(limit)
    section = '\n{}\nViolations count: {}'.format(title, violationscount)
    if cntExceptions > 0:
        section += ' (+ {} exceptions)'.format(cntExceptions)
    section += '\n'
    cnt = 0
    for line in violations:
        cnt += 1
        section += line + '\n'
        if cnt > 5000:
            section += 'Too many results. {} records skipped.\n'.format(len(violations)-5000)
            break
    if limit > 0:
        section += 'Too many results.\n'
    return section


def main():
    properties = AllpagesPageGenerator(namespace=120)
    for property in properties:
        try:
            p = property.title().replace('Property:', '')       # property id
            ppage = pywikibot.PropertyPage(repo, p)             # property page
            tpage = pywikibot.Page(site, 'Property talk:'+p)    # property talk page
            #  if tpage.exists() and ppage.exists() #  deactivated due to pywikibot bug
            if tpage.exists():
                ppage.get()
                talkpage = re.sub(r'{{(q|Q)\|q?Q?(\d+)}}', r'Q\2', tpage.get())
                talkpage = re.sub(r'{{(p|P)\|p?P?(\d+)}}', r'P\2', talkpage)
                wikicode = mwparserfromhell.parse(talkpage)
                templates = wikicode.filter_templates()
                report = u''
                for t in templates:
                    if t.name in types:
                        try:
                            report += oneConstraint(p, ppage.type, t)  # create report for one constraint
                        except Exception, e:
                            logwrite(str(e) + '\n')
                if len(report) > 1:
                    try:
                        query = 'SELECT (count(DISTINCT(?item)) AS ?cnt) WHERE {{ {{ ?item wdt:{p} [] . }} UNION {{ ?ref pr:{p} [] . ?statement1 prov:wasDerivedFrom ?ref . ?item ?p1 ?statement1 }} UNION {{ ?statement1 pq:{p} [] . ?item ?p1 ?statement1 }} }}'.format(p=p)
                        data, _ = requestquery(query)
                        cnt = data['results']['bindings'][0]['cnt']['value']
                    except:
                        cnt = ''
                    report = header.format(time.strftime("%Y-%m-%d %H:%M (%Z)"), cnt) + report
                    cpage = pywikibot.Page(site, 'Wikidata:Database reports/Constraint violations/'+p)
                    cpage.put(report, comment='report update for [[Property:'+p+']]', minorEdit=False)
        except Exception, e:
            logwrite(str(e) + '\n')


if __name__ == "__main__":
    main()
