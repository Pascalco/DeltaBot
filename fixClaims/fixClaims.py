# -*- coding: utf-8  -*-
import re
import sys
import requests
import pywikibot
import json
import string

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()
siteCommons = pywikibot.Site('commons', 'commons')
repoCommons = siteCommons.data_repository()

f2 = open('fixClaims/isbn_range.xml', encoding='utf-8').read().replace('\n', '').replace(' ', '')
exec(open('fixClaims/categoryPrefix.dat', encoding='utf-8').read())

whitelist = ['Q4115189', 'Q13406268', 'Q15397819']

#########################
# format actions        #
#########################


def format_uppercase(value, job):
    return value.upper()


def format_lowercase(value, job):
    return value.lower()


def format_removeLast(value, job):
    return value[:-1]


def format_removeFirst(value, job):
    return value[1:]


def format_removeWhitespace(value, job):
    return value.replace(' ', '')


def format_isniformat(value, job):
    value = re.sub(r'[^0-9X]', '', value)
    return value[0:4] + ' ' + value[4:8] + ' ' + value[8:12] + ' ' + value[12:16]


def format_dash(value, job):
    return (value.encode('utf-8').replace('-', '–')).decode('utf-8')


def format_removePrefix(value, job):
    for _ in range(0, len(value)):
        value = value[1:]
        if formatcheck(value, job['regex']):
            return value
    return None


def format_removeSuffix(value, job):
    for _ in range(0, len(value)):
        value = value[:-1]
        if formatcheck(value, job['regex']):
            return value
    return None


def format_add0(value, job):
    for _ in range(10):
        value = '0'+value
        if formatcheck(value, job['regex']):
            return value
    return None


def format_linkedin(value, job):
    newvalue = re.sub(r'https?://(.*)linkedin\.com/in/', 'https://www.linkedin.com/in/', value)
    if newvalue[-1] == '/':
        return newvalue[:-1]
    else:
        return newvalue


def format_isbn10(value, job):
    val = value.replace('-', '').replace(' ', '')
    if len(val) != 10:
        return None
    if int(val[0]) == 6:
        country = val[0:3]
        rest = val[3:]
        rest2 = int(val[3:])
    elif int(val[0]) <= 7:
        country = val[0]
        rest = val[1:]
        rest2 = int(val[1:8])
    elif int(val[0:2]) <= 94:
        country = val[0:2]
        rest = val[2:]
        rest2 = int(val[2:9])
    elif int(val[0:3]) <= 989:
        country = val[0:3]
        rest = val[3:]
        rest2 = int(val[3:9])*10
    elif int(val[0:4]) <= 9984:
        country = val[0:4]
        rest = val[4:]
        rest2 = int(val[4:9])*100
    else:
        country = val[0:5]
        rest = val[5:]
        rest2 = int(val[5:9])*1000

    res = re.findall(r'<Prefix>978-'+country+'</Prefix>([^G]*)', f2)
    if not res:
        return None
    for m in res:
        res2 = re.findall(r'<Range>([0-9]*)-([0-9]*)</Range><Length>([0-9])</Length>', m)
        if res2:
            for n in res2:
                if rest2 >= int(n[0]) and rest2 <= int(n[1]):
                    publisher = rest[0:int(n[2])]
                    work = rest[int(n[2]):-1]
                    return country+'-'+publisher+'-'+work+'-'+val[9]


def format_uuid(value, job):
    val = value.replace('-', '').replace(' ', '')
    if len(val) != 32:
        return None
    return value[0:8] + '-' + value[8:12] + '-' + value[12:16] + '-' + value[16:20] + '-' + value[20:32]


#########################
# actions               #
#########################


def action_format(item, job):
    for claim in item.claims[job['p']]:
        if formatcheck(claim, job['regex']):
            continue
        subaction = globals()['format_' + job['subaction']]
        newVal = subaction(claim.getTarget(), job)
        if newVal:
            if formatcheck(newVal, job['regex']):
                claim.changeTarget(newVal)


def action_normalize(item, job):
    for claim in item.claims[job['p']]:
        m = claim.toJSON()
        curVal = m['mainsnak']['datavalue']['value']
        newVal = curVal.replace('_', ' ')
        if newVal[0:5] == 'File:':
            newVal = newVal[5:]
        target = pywikibot.FilePage(siteCommons, newVal)
        if target.exists():
            claim.changeTarget(target)


#correct wrong authority identfiers with the value from VIAF
def action_viaf(item, job):
    for m in item.claims['P214']:
        viaf  = m.getTarget()
        for claim in item.claims[job['p']]:
            value = claim.getTarget()
            r = requests.get('https://viaf.org/viaf/' + viaf + '/viaf.json')
            data = r.json()
            if 'ns0:redirect' in data:
                r = requests.get('https://viaf.org/viaf/' + data['ns0:redirect']['ns0:directto'] + '/viaf.json')
                data = r.json()
            if not isinstance(data['ns1:sources']['ns1:source'], list):
                sources = [data['ns1:sources']['ns1:source']]
            else:
                sources = data['ns1:sources']['ns1:source']
            for n in sources:
                if job['viafkey'] in n['#text']:
                    viafvalue = n['@nsid']
                    if job['p'] == 'P268':
                        viafvalue = viafvalue.replace('http://catalogue.bnf.fr/ark:/12148/cb', '')
                    elif job['p'] == 'P227':
                        viafvalue = viafvalue.replace('http://d-nb.info/gnd/', '')
                    elif job['p'] == 'P1273':
                        viafvalue = viafvalue[1:]
                    if job['p'] == 'P227':
                        if 'DNB|'+value != n['#text']:
                            continue
                    else:
                        if levenshtein(value, viafvalue) > 2:
                            continue
                    if formatcheck(viafvalue, job['regex']):
                        claim.changeTarget(viafvalue)
                        break


#add an inverse claim
def action_inverse(item, job):
    #bug with checking for same claim
    itemID = item.getID()
    for claim in item.claims[job['p']]:
        target = claim.getTarget()
        if not target:
            continue
        if target.isRedirectPage():
            continue
        if not target.exists():
            continue
        target.get()
        if 'constrainttarget' in job:
            if not constraintTargetCheck(target, job):
                continue
        ok = True
        if target.claims:
            if job['pNewT'] in target.claims:
                for m in target.claims[job['pNewT']]:
                    if m.getTarget() is None:
                        continue
                    if m.getTarget().getID() == itemID:
                        ok = False
                        break
        if ok:
            claimNew = pywikibot.Claim(repo, job['pNewT'])
            claimNew.setTarget(item)
            target.addClaim(claimNew, summary=u'adding inverse claim')
            source = pywikibot.Claim(repo, 'P3452')
            source.setTarget(item)
            claimNew.addSource(source)


# change property from pOld to pNew.
# if pNew is already added with the same value, only pOld gets removed
def action_changeProperty(item, job):
    if not job['pOld'] in item.claims:
        return 0
    for claim in item.claims[job['pOld']]:
        if 'constraintvalue' in job:
            if not constraintValueCheck(claim.getTarget(), job):
                continue
        m = claim.toJSON()
        mydata = {}
        mydata['claims'] = [{"id": m['id'], "remove":""}]
        d = item.claims.get(job['pNew'], [])
        for n in d:
            if claim.getTarget() == n.getTarget():
                break
        else:
            m['mainsnak']['property'] = job['pNew']
            m.pop('id', None)
            mydata['claims'].append(m)
        item.editEntity(mydata, summary=u'change property [[Property:'+job['pOld']+']] -> [[Property:'+job['pNew']+']]')


# change property of qualifier on claim p from pOld to pNew
# if pNew is already set as qualifier, no action is taken
def action_changeQualifierProperty(item, job):
    data = item.toJSON()
    for m in data['claims'][job['p']]:
        if 'qualifiers' not in m:
            continue
        if job['pOld'] not in m['qualifiers']:
            continue
        if job['pNew'] in m['qualifiers']:
            continue
        m['qualifiers'][job['pNew']] =  m['qualifiers'][job['pOld']]
        for x in m['qualifiers'][job['pNew']]:
            x['hash'] = ''
            x['property'] = job['pNew']
        del m['qualifiers'][job['pOld']]
        m['qualifiers-order'] = [w.replace(job['pOld'], job['pNew']) for w in m['qualifiers-order']]
        mydata = {}
        mydata['claims'] = [m]
        item.editEntity(mydata, summary=u'change qualifier [[Property:'+job['pOld']+']] -> [[Property:'+job['pNew']+']]')


#add claim pNew=valNew
def action_addClaim(item, job):
    if job['pNew'] in item.claims:
        return 0
    claimNew = pywikibot.Claim(repo, job['pNew'])
    if 'valNew' in job:
        newvalue = pywikibot.ItemPage(repo, job['valNew'])
    elif 'fromSitelink' in job:
        if job['fromSitelink'] not in item.sitelinks:
            return 0
        newvalue = item.sitelinks[job['fromSitelink']]
        if 'removenamespace' in job:
            newvalue = newvalue.split(':')[0]
    else:
        return 0
    claimNew.setTarget(newvalue)
    item.addClaim(claimNew)


#add value claim pNew=valNew
def action_addValueClaim(item, job):
    for claim in item.claims[job['p']]:
        target = claim.getTarget()
        if target.isRedirectPage():
            continue
        if not target.exists():
            continue
        target.get()
        if 'constrainttarget' in job:
            if not constraintTargetCheck(target, job):
                continue
        if job['pNewT'] not in target.claims:
            claimNew = pywikibot.Claim(repo, job['pNewT'])
            itemNew = pywikibot.ItemPage(repo, job['valNew'])
            claimNew.setTarget(itemNew)
            target.addClaim(claimNew)


def action_changeValue(item, job):
    for claim in item.claims[job['p']]:
        m = claim.toJSON()
        if 'datavalue' not in m['mainsnak']:
            continue
        curVal = str(m['mainsnak']['datavalue']['value']['numeric-id'])
        if curVal not in job['map']:
            continue
        newVal = job['map'][curVal]
        mydata = {}
        m['mainsnak']['datavalue']['value']['numeric-id'] = newVal
        mydata['claims'] = [m]
        summary = u'change value of [[Property:' + job['p'] + ']]: [[Q' + curVal + ']] -> [[Q' + str(newVal) + ']]'
        item.editEntity(mydata, summary=summary)


def action_removeStatement(item, job):
    for claim in item.claims[job['p']]:
        if 'constraintvalue' in job:
            if not constraintValueCheck(claim.getTarget(), job):
                continue
        item.removeClaims(claim, summary=job['summary'])


def action_removeUnit(item, job):
    for claim in item.claims[job['p']]:
        m = claim.toJSON()
        mydata = {}
        m['mainsnak']['datavalue']['value']['unit'] = '1'
        mydata['claims'] = [m]
        summary = u'remove unit from [[Property:' + job['p'] + ']]'
        item.editEntity(mydata, summary=summary)


def action_moveStatementToQualifier(item, job):
    if job['pNew'] not in item.claims:
        return 0
    if len(item.claims[job['pNew']]) != 1:
        return 0
    data = item.toJSON()
    mydata = {}
    mydata['claims'] = []
    m = data['claims'][job['pNew']][0]
    if 'qualifiers' not in m:
        m['qualifiers'] = {}
    if job['p'] not in m['qualifiers']:
        m['qualifiers'][job['p']] = []
    for claim in data['claims'][job['p']]:
        mydata['claims'].append({'id':claim['id'], 'remove': ''})
        m['qualifiers'][job['p']].append(claim['mainsnak'])
    mydata['claims'].append(m)
    summary = u'move claim [[Property:'+job['p']+']] -> [[Property:'+job['pNew']+']]'
    item.editEntity(mydata, summary=summary)


def action_moveQualifierToStatement(item, job):
    if job['pOld'] not in item.claims:
        return 0
    mydata = {}
    mydata['claims'] = []
    for claim in item.claims[job['pOld']]:
        if claim.getTarget().getID() == job['valueOld']:
            if job['pQualifier'] in claim.qualifiers:
                data = claim.toJSON()
                mydata['claims'].append({'id':data['id'], 'remove': ''})
                ok = True
                value = claim.qualifiers[job['pQualifier']][0].getTarget()
                if job['pNew'] in item.claims:
                    for c in item.claims[job['pNew']]:
                        if c.getTarget() == value:
                            ok = False
                if ok:
                    data['mainsnak']['property'] = job['pNew']
                    data['mainsnak']['datavalue'] = data['qualifiers'][job['pQualifier']][0]['datavalue']
                    del data['qualifiers'][job['pQualifier']][0]
                    del data['id']
                    mydata['claims'].append(data)
    summary = u'move claim [[Property:'+job['pOld']+']] -> [[Property:'+job['pNew']+']]'
    item.editEntity(mydata, summary=summary)


def action_moveSourceToQualifier(item, job):
    for prop in item.claims.keys():
        for claim in item.claims[prop]:
            data = claim.toJSON()
            i = -1
            for source in claim.sources:
                i += 1
                if job['p'] not in source:
                    continue
                for snak in source[job['p']]:
                    data['qualifiers'] = data.get('qualifiers', {})
                    data['qualifiers'][job['p']] = data['qualifiers'].get(job['p'], [])
                    for qual in (pywikibot.Claim.qualifierFromJSON(repo, q) for q in data['qualifiers'][job['p']]):
                        if str(qual.getTarget()) == str(snak.getTarget()):
                            break
                    else:
                        snak.isReference = False
                        snak.isQualifier = True
                        data['qualifiers'][job['p']].append(snak.toJSON())
                    data['references'][i]['snaks'][job['p']].pop(0)
                    if len(data['references'][i]['snaks'][job['p']]) == 0:
                        data['references'][i]['snaks'].pop(job['p'])
                        if len(data['references'][i]['snaks']) == 0:
                            data['references'].pop(i)
                            i -= 1
            mydata = {'claims': [data]}
            summary = u'move reference [[Property:' + job['p'] + ']] to qualifier'
            item.editEntity(mydata, summary=summary)


def action_moveQualifierToSource(item, job):
    for prop in item.claims.keys():
        for claim in item.claims[prop]:
            data = claim.toJSON()
            if job['p'] not in claim.qualifiers:
                continue
            for snak in claim.qualifiers[job['p']]:
                ok = True
                data['references'] = data.get('references', [])
                for reference in data['references']:
                    for _, ref in pywikibot.Claim.referenceFromJSON(repo, reference).items():
                        for x in ref:
                            if str(snak.getTarget()) == str(x.getTarget()):
                                ok = False
                if ok:
                    snak.isQualifier = False
                    snak.isReference = True
                    data['references'].append({'snaks': {job['p']: [snak.toJSON()]}})
                data['qualifiers'][job['p']].pop(0)
                if len(data['qualifiers'][job['p']]) == 0:
                    data['qualifiers'].pop(job['p'])
            mydata = {'claims': [data]}
            summary = u'move qualifier [[Property:' + job['p'] + ']] to reference'
            item.editEntity(mydata, summary=summary)


#########################
# checks                #
#########################


def constraintTargetCheck(item, job):
    for constraint in job['constrainttarget']:
        check = globals()['check_' + constraint['type']]
        if not check(item, constraint):
            return False
    return True


def constraintCheck(item, job):
    for constraint in job['constraint']:
        check = globals()['check_' + constraint['type']]
        if not check(item, constraint):
            return False
    return True


def constraintValueCheck(value, job):
    for constraint in job['constraintvalue']:
        check = globals()['check_' + constraint['type']]
        if not check(value, constraint):
            return False
    return True


def check_item(item, constraint):
    item.get()
    if not constraint['p'] in item.claims:
        return False
    if 'val' in constraint:
        if isinstance(constraint['val'], str):
            constraint['val'] = [constraint['val']]
        if not item.claims[constraint['p']][0].getTarget().getID() in constraint['val']:
            #TODO: don't check only first claim in statement
            return False
    return True


def check_category(item, constraint):
    for s in item.sitelinks:
        prefix = item.sitelinks[s].split(':')[0]
        if prefix not in categoryPrefix:
            return False
    return True


def check_oneof(value, constraint):
    if isinstance(value, pywikibot.ItemPage):
        value = value.getID()
    if value in constraint['values']:
        return True
    return False


def check_format(value, constraint):
    return formatcheck(value, constraint['regex'])


def formatcheck(claim, regex):
    if isinstance(claim, str):
        value = claim
    elif isinstance(claim, pywikibot.FilePage):
        value = claim.title()
    else:
        value = claim.getTarget()
    return bool(re.fullmatch(regex, value))


def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

#########################
# main functions        #
#########################


#find on Wikidata:Dabase_reports violations
def getViolations(job):
    candidates = []
    payload = {
        'query': job['query'],
        'format': 'json'
    }
    r = requests.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql?', params=payload)
    try:
        data = r.json()
        for m in data['results']['bindings']:
            candidates.append(m['item']['value'].replace('http://www.wikidata.org/entity/', ''))
    except:
        pass
    return candidates


def proceedOneCandidate(q, job):
    if q[0] != 'Q':
        return 0
    item = pywikibot.ItemPage(repo, q)
    if item.isRedirectPage():
        return 0
    if not item.exists():
        return 0
    item.get()
    #checks
    if 'constraint' in job:
        if not constraintCheck(item, job):
            return 0
    #actions
    action = globals()['action_' + job['action']]
    action(item, job)


def main():
    r = requests.get('https://www.wikidata.org/wiki/User:DeltaBot/fixClaims/jobs?action=raw')
    jobs = r.json()
    done = json.load(open('fixClaims/done.json', encoding='utf-8'))
    for job in jobs:
        candidates = getViolations(job)
        if job['name'] not in done:
            done[job['name']] = []
        for q in candidates:
            if q not in done[job['name']] and q not in whitelist:
                try:
                    proceedOneCandidate(q, job)
                    done[job['name']].append(q)
                except:
                    pass
    f1 = open('fixClaims/done.json', 'w', encoding='utf-8')
    f1.write(json.dumps(done, ensure_ascii=False))
    f1.close()


if __name__ == "__main__":
    main()
