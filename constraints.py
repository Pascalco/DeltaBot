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
import datetime
import pywikibot
from pywikibot.pagegenerators import *

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

types = ['Q21503250', 'Q21510865', 'Q21510862', 'Q21510855', 'Q21502410', 'Q19474404', 'Q21510857', 'Q21503247', 'Q21510864', 'Q21514353', 'Q21510860', 'Q21510851', 'Q21510856', 'Q21528958', 'Q21510863', 'Q21528959', 'Q21502404', 'Q21510859', 'Q21502838', 'Q25796498']
#missing_types = ['Q21510852', 'Q21510854']
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


def oneConstraint(p, datatype, constraint):
    # make list of exceptions
    if 'P2303' in constraint.qualifiers:
        exceptions = [val.getTarget().getID() for val in constraint.qualifiers['P2303']]
    else:
        exceptions = []

    constrainttype = constraint.getTarget().getID()

    # write query
    if constrainttype == 'Q21503250': # Constraint:Type
        relation = 'P279' if constraint.qualifiers['P2309'][0].getTarget().getID() == 'Q21514624' else 'P31' #ToDo: instance or subclass (Q30208840)
        list = [val.getTarget().getID() for val in constraint.qualifiers['P2308']]
        classes = 'wd:' + ', wd:'.join(list)
        query = 'SELECT DISTINCT ?item WHERE{{ ?item wdt:{p} [] . MINUS {{ ?item wdt:{relation}/wdt:P279* ?class . FILTER(?class IN ({classes})) }} }}'.format(p=p, relation=relation, classes=classes)
        title = '<span id="Type {}"></span>\n== "Type {{{{Q|{}}}}}" violations =='.format(', '.join(list), '}}, {{Q|'.join(list))

    elif constrainttype == 'Q21510865': # Constraint:Value type
        relation = 'P279' if constraint.qualifiers['P2309'][0].getTarget().getID() == 'Q21514624' else 'P31' #ToDo: instance or subclass (Q30208840)
        list = [val.getTarget().getID() for val in constraint.qualifiers['P2308']]
        classes = 'wd:' + ', wd:'.join(list)
        query = 'SELECT DISTINCT ?item WHERE{{ ?item wdt:{p} ?value . MINUS {{ ?value wdt:{relation}/wdt:P279* ?class . FILTER(?class IN ({classes})) }} }}'.format(p=p, relation=relation, classes=classes)
        title = '<span id="Value type {}"></span>\n== "Value type {{{{Q|{}}}}}" violations =='.format(','.join(list), '}}, {{Q|'.join(list))

    elif constrainttype == 'Q21510862': # Constraint:Symmetric
        query = 'SELECT DISTINCT ?item {{ ?item wdt:{p} ?value . MINUS {{ ?value wdt:{p} ?item . }} }}'.format(p=p)
        title = '<span id="Symmetric"></span>\n== "Symmetric" violations =='

    elif constrainttype == 'Q21510855': # Constraint:Inverse
        property = constraint.qualifiers['P2306'][0].getTarget().getID()
        query = 'SELECT DISTINCT ?item WHERE {{ ?inverse wdt:{p} ?item FILTER NOT EXISTS {{ ?item wdt:{property} ?inverse }} }}'.format(p=p, property=property)
        title = '<span id="Inverse"></span>\n== "Inverse" violations =='

    elif constrainttype == 'Q21502410': # Constraint:Unique value/Distinct value
        query = 'SELECT DISTINCT ?item (COUNT(?item1) AS ?count)(GROUP_CONCAT(?item1;separator=",") AS ?items) WHERE {{ ?item1 wdt:{p} ?item }} GROUP BY ?item HAVING(?count > 1)1'.format(p=p)
        title = '<span id="Unique value"></span>\n== "Unique value" violations =='
        variables = ['items']

    elif constrainttype == 'Q19474404': # Constraint:Single value
        query = 'SELECT DISTINCT ?item (COUNT(?value) AS ?count)(GROUP_CONCAT(?value;separator=", ") AS ?values) WHERE {{ ?item wdt:{p} ?value }} GROUP BY ?item HAVING(?count > 1)'.format(p=p)
        title = '<span id="Single value"></span>\n== "Single value" violations =='
        variables = ['values']

    elif constrainttype == 'Q21510857': # Constraint:Multi values
        query = 'SELECT DISTINCT ?item (COUNT(?value) AS ?count) {{ ?item wdt:{p} ?value .}} GROUP BY ?item HAVING (?count=1)'.format(p=p)
        title = '<span id="Multi value"></span>\n== "Multi value" violations =='

    elif constrainttype == 'Q21503247': # Constraint:Item
        property = constraint.qualifiers['P2306'][0].getTarget().getID()
        if 'P2305' in constraint.qualifiers:
            list = [val.getTarget().getID() for val in constraint.qualifiers['P2305']]
            items = 'wd:' + ', wd:'.join(list)
            query = 'SELECT DISTINCT ?item WHERE {{ ?item wdt:{p} [] . MINUS {{ ?item wdt:{property} ?values . FILTER (?values IN ({items})) }} }}'.format(p=p, property=property, items=items)
        else:
            query = 'SELECT DISTINCT ?item WHERE {{ ?item wdt:{p} [] . MINUS {{ ?item wdt:{property} [] }} }}'.format(p=p, property=property)
        title = '<span id="Item {0}"></span>\n== "Item {{{{P|{0}}}}}" violations =='.format(property)

    elif constrainttype == 'Q21510864': # Constraint:Target required claim
        property = constraint.qualifiers['P2306'][0].getTarget().getID()
        if 'P2305' in constraint.qualifiers:
            list = [val.getTarget().getID() for val in constraint.qualifiers['P2305']]
            items = 'wd:' + ', wd:'.join(list)
            query = 'SELECT DISTINCT ?item WHERE {{ ?item wdt:{p} ?target . MINUS {{ ?target wdt:{property} ?values . FILTER (?values IN ({items})) }} }}'.format(p=p, property=property, items=items)
        else:
            query = 'SELECT DISTINCT ?item WHERE {{ ?item wdt:{p} ?target . MINUS {{ ?target wdt:{property} [] }} }}'.format(p=p, property=property)
        title = '<span id="Target required claim {0}"></span>\n== "Target required claim {{{{P|{0}}}}}" violations =='.format(property)

    elif constrainttype == 'Q21514353': # Constraint:Units
        if constraint.qualifiers['P2305'][0].snaktype == 'novalue':
            units = 'wd:Q199'
        else:
            list = [val.getTarget().getID() for val in constraint.qualifiers['P2305']]
            units = 'wd:' + ', wd:'.join(list)
        query = 'SELECT DISTINCT ?item ?unit WHERE {{ ?item p:{p}/psv:{p}/wikibase:quantityUnit ?unit FILTER (?unit NOT IN ({units})) }}'.format(p=p, units=units)
        title = '<span id="Units"></span>\n== "Units" violations =='
        variables = ['unit']

    elif constrainttype == 'Q21510860': # Constraint:Range
        if datatype == 'time':
            if constraint.qualifiers['P2310'][0].snaktype == 'somevalue':
                min = time.strftime('%Y')
            else:
                min = constraint.qualifiers['P2310'][0].getTarget().year
            if constraint.qualifiers['P2311'][0].snaktype == 'somevalue':
                max = time.strftime('%Y')
            else:
                max = constraint.qualifiers['P2311'][0].getTarget().year
            query = 'SELECT DISTINCT ?item ?value WHERE {{ ?item wdt:{p} ?value FILTER (year(?value) < {min} || year(?value) > {max}) }}'.format(p=p, min=min, max=max)
        else:
            min = constraint.qualifiers['P2313'][0].getTarget().amount
            max = constraint.qualifiers['P2312'][0].getTarget().amount
            query = 'SELECT DISTINCT ?item ?value WHERE {{ ?item wdt:{p} ?value FILTER (?value < {min} || ?value > {max}) }}'.format(p=p, min=min, max=max)
        title = '<span id="Range"></span>\n== "Range" violations =='
        variables = ['value']

    elif constrainttype == 'Q21510851': # Constraint:Allowed Qualifiers
        if constraint.qualifiers['P2306'][0].snaktype == 'novalue':
            query = 'SELECT DISTINCT ?item ?qual WHERE {{ hint:Query hint:optimizer "None" . ?item p:{p} ?statement . ?statement ?pq_qual ?pq_obj . ?qual wikibase:qualifier ?pq_qual }}'.format(p=p)
        else:
            list = [val.getTarget().getID() for val in constraint.qualifiers['P2306']]
            qualifiers = 'wd:' + ', wd:'.join(list)
            query = 'SELECT DISTINCT ?item ?qual WHERE {{ hint:Query hint:optimizer "None" . ?item p:{p} ?statement . ?statement ?pq_qual ?pq_obj . ?qual wikibase:qualifier ?pq_qual . FILTER (?qual NOT IN ({qualifiers})) }}'.format(p=p, qualifiers=qualifiers)
        title = '<span id="Allowed Qualifiers"></span>\n== "Allowed Qualifiers" violations =='
        variables = ['qual']

    elif constrainttype == 'Q21510856': # Constraint:Mandatory Qualifiers
        list = [val.getTarget().getID() for val in constraint.qualifiers['P2306']]
        qualifiers = 'pq:' + ' []; pq:'.join(list)
        query = 'SELECT DISTINCT ?item WHERE {{ ?item p:{p} ?statement . MINUS {{ ?statement {qualifiers} [] }} }}'.format(p=p, qualifiers=qualifiers)
        title = '<span id="Mandatory Qualifiers"></span>\n== "Mandatory Qualifiers" violations =='

    elif constrainttype == 'Q21528958': # Constraint:Value only
        query = 'SELECT DISTINCT ?item WHERE {{ {{ ?statement0 pq:{p} ?value . ?item ?p0 ?statement0 . ?prop wikibase:claim ?p0 . FILTER(?prop != wd:P1855 && ?prop != wd:P2271) }} UNION {{ ?ref pr:{p} ?value . ?statement1 prov:wasDerivedFrom ?ref . ?item ?p1 ?statement1 }} }}'.format(p=p)
        title = '<span id="Value only"></span>\n== "Value only" violations =='

    elif constrainttype == 'Q21510863': # Constraint:Qualifier
        query = 'SELECT DISTINCT ?item WHERE {{ {{ ?item wdt:{p} ?value . }} UNION {{ ?ref pr:{p} ?value . ?statement1 prov:wasDerivedFrom ?ref . ?item ?p1 ?statement1  }} }}'.format(p=p)
        title = '<span id="Qualifier"></span>\n== "Qualifier" violations =='

    elif constrainttype == 'Q21528959': # Constraint:Source only
        query = 'SELECT DISTINCT ?item {{ {{ ?item wdt:{p} ?value . }} UNION { ?statement1 pq:{p} ?value . ?item ?p1 ?statement1 }} }}'.format(p=p)
        title = '<span id="Source only"></span>\n== "Source only" violations =='

    elif constrainttype == 'Q21502404': # Constraint:Format
        pattern = constraint.qualifiers['P1793'][0].getTarget().replace('\\', '\\\\').replace('"', '\\"')
        if pattern[0] == '^':
            pattern = pattern[1:]
        if pattern[-1] == '$':
            pattern = pattern[:-1]
        if datatype == 'commonsMedia':
            pattern = pattern.replace(' ', '%20')
            pattern = 'http://commons.wikimedia.org/wiki/Special:FilePath/' + pattern
        query = 'SELECT DISTINCT ?item ?value WHERE {{ {{ ?item wdt:{p} ?value }} UNION {{ ?statement1 pq:{p} ?value . ?item ?p1 ?statement1 . }} UNION {{ ?ref pr:{p} ?value . ?statement2 prov:wasDerivedFrom ?ref . ?item ?p2 ?statement2 . }} .  FILTER( REGEX(STR(?value), "^{pattern}$") = false ) }}'.format(p=p, pattern=pattern)
        title = '<span id="Format"></span>\n== "Format" violations =='
        variables = ['value']

    elif constrainttype == 'Q21510859': # Constraint:One of
        list = [val.getTarget() for val in constraint.qualifiers['P2305']]
        if None in list: list.remove(None)
        list = [l.getID() for l in list]
        values = 'wd:' + ', wd:'.join(list)
        query = 'SELECT DISTINCT ?item ?value WHERE {{ {{ ?item p:{p}/ps:{p} ?value	}} UNION {{ ?statement1 pq:{p} ?value . ?item ?p1 ?statement1 . }} UNION {{	?ref pr:{p} ?value . ?statement2 prov:wasDerivedFrom ?ref. ?item ?p2 ?statement2 . }} FILTER (?value NOT IN ({values})) }}'.format(p=p, values=values)
        title = '<span id="One of"></span>\n== "One of" violations =='
        variables = ['value']

    elif constrainttype == 'Q21502838': #Constraint:Conflict with
        property = constraint.qualifiers['P2306'][0].getTarget().getID()
        if 'P2305' in constraint.qualifiers:
            list = [val.getTarget() for val in constraint.qualifiers['P2305']]
            if None in list: list.remove(None)
            list = [l.getID() for l in list]
            values = 'wd:' + ' wd:'.join(list)
            query = 'SELECT DISTINCT ?item ?value WHERE {{?item wdt:{p} [] . VALUES ?value {{ {values} }} . ?item wdt:{property} ?value .}}'.format(p=p, property=property, values=values)
        else:
            query = 'SELECT DISTINCT ?item ?value WHERE {{?item wdt:{p} [] . ?item wdt:{property} ?value .}}'.format(p=p, property=property)
        title = '<span id="Conflicts with"></span>\n== "Conflicts with" violations =='
        variables = ['value']

    elif constrainttype == 'Q25796498': #Constraint:contemporary
        query = 'SELECT DISTINCT ?item WHERE {{ ?item wdt:{p} ?value . OPTIONAL {{ ?item p:P569/psv:P569 [ wikibase:timeValue ?item_birth ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?value p:P569/psv:P569 [ wikibase:timeValue ?value_birth ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?item p:P571/psv:P571 [ wikibase:timeValue ?item_inception ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?value p:P571/psv:P571 [ wikibase:timeValue ?value_inception ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?item p:P580/psv:P580 [ wikibase:timeValue ?item_start ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?value p:P580/psv:P580 [ wikibase:timeValue ?value_start ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?item p:P570/psv:P570 [ wikibase:timeValue ?item_death ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?value p:P570/psv:P570 [ wikibase:timeValue ?value_death ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?item p:P576/psv:P576 [ wikibase:timeValue ?item_dissolution ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?value p:P576/psv:P576 [ wikibase:timeValue ?value_dissolution ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?item p:P582/psv:P582 [ wikibase:timeValue ?item_end ; wikibase:timePrecision "11"^^xsd:integer ] . }} OPTIONAL {{ ?value p:P582/psv:P582 [ wikibase:timeValue ?value_end ; wikibase:timePrecision "11"^^xsd:integer ] . }} FILTER ((!BOUND(?item_birth) || ((!BOUND(?value_death) || ?item_birth>?value_death) && (!BOUND(?value_dissolution) || ?item_birth>?value_dissolution) && (!BOUND(?value_end) || ?item_birth>?value_end))) && (!BOUND(?value_birth) || ((!BOUND(?item_death) || ?value_birth>?item_death) && (!BOUND(?item_dissolution) || ?value_birth>?item_dissolution) && (!BOUND(?item_end) || ?value_birth>?item_end))) && (!BOUND(?item_inception) || ((!BOUND(?value_death) || ?item_inception>?value_death) && (!BOUND(?value_dissolution) || ?item_inception>?value_dissolution) && (!BOUND(?value_end) || ?item_inception>?value_end))) && (!BOUND(?value_inception) || ((!BOUND(?item_death) || ?value_inception>?item_death) && (!BOUND(?item_dissolution) || ?value_inception>?item_dissolution) && (!BOUND(?item_end) || ?value_inception>?item_end))) && (!BOUND(?item_start) || ((!BOUND(?value_death) || ?item_start>?value_death) && (!BOUND(?value_dissolution) || ?item_start>?value_dissolution) && (!BOUND(?value_end) || ?item_start>?value_end))) && (!BOUND(?value_start) || ((!BOUND(?item_death) || ?value_start>?item_death) && (!BOUND(?item_dissolution) || ?value_start>?item_dissolution) && (!BOUND(?item_end) || ?value_start>?item_end))) && ((BOUND(?item_birth) && (BOUND(?value_death) || BOUND(?value_dissolution) || BOUND(?value_end))) || (BOUND(?value_birth) && (BOUND(?item_death) || BOUND(?item_dissolution) || BOUND(?item_end))) || (BOUND(?item_inception) && (BOUND(?value_death) || BOUND(?value_dissolution) || BOUND(?value_end))) || (BOUND(?value_inception) && (BOUND(?item_death) || BOUND(?item_dissolution) || BOUND(?item_end))) || (BOUND(?item_start) && (BOUND(?value_death) || BOUND(?value_dissolution) || BOUND(?value_end))) || (BOUND(?value_start) && (BOUND(?item_death) || BOUND(?item_dissolution) || BOUND(?item_end))))) }}'.format(p=p)
        title = '<span id="contemporary"></span>\n== "Contemporary" violations =='

    # execute query, if necessary limit number of results
    try:
        data, limit = requestquery(query, 0)
    except:
        try:
            data, limit = requestquery(query, 5000)
        except:
            logwrite('error with ' + p + ' : ' + constrainttype + '\n' + query + '\n')
            return ''
    d = sorted(data['results']['bindings'], key=lambda x: (int(x['item']['value'][32:]) if x['item']['value'][32:].isdigit() else float('inf'), x['item']['value']))
    violations = []
    cntExceptions = 0
    for m in d:
        qid = m['item']['value'].replace('http://www.wikidata.org/entity/', '')
        link = 1
        if constrainttype == 'Q21502410':
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
                        tt = [t.replace('P', 'Property:P') for t in tt]
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
            ppage.get()
            if 'P2302' not in ppage.claims:
                continue
            cpage = pywikibot.Page(site, 'Wikidata:Database reports/Constraint violations/'+p)
            if cpage.exists():
                lastedit = cpage.getVersionHistory()[0]
                if (datetime.datetime.now()-lastedit[1]).days < 1:
                    continue
                if lastedit[2] == 'KrBot2' and 'ERROR:' not in cpage.text:
                    continue
            report = u''
            for co in ppage.claims['P2302']:
                if co.getTarget().getID() in types:
                    try:
                        report += oneConstraint(p, ppage.type, co)  # create report for one constraint
                    except Exception, e:
                        logwrite(str(e) + '\n')
            if len(report) > 1:
                try:
                    query = 'SELECT (count(DISTINCT(?item)) AS ?cnt) WHERE {{ {{ ?item wdt:{p} [] . }} UNION {{ ?ref pr:{p} [] . ?statement1 prov:wasDerivedFrom ?ref . ?item ?p1 ?statement1 }} UNION {{ ?statement1 pq:{p} [] . ?item ?p1 ?statement1 }} }}'.format(p=p)
                    data, _ = requestquery(query)
                    cnt = data['results']['bindings'][0]['cnt']['value']
                except:
                    cnt = ''
                report = header.format(time.strftime("%Y-%m-%dT%H:%M:%SZ"), cnt) + report
                cpage.put(report, comment='report update for [[Property:'+p+']]', minorEdit=False)
        except Exception, e:
            logwrite(str(e) + '\n')


if __name__ == "__main__":
    main()
