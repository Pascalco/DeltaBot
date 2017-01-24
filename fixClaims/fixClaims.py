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

f2 = open('fixClaims/isbn_range.xml').read().replace('\n', '').replace(' ', '')
execfile('fixClaims/categoryPrefix.dat')

whitelist = ['Q4115189', 'Q13406268', 'Q15397819']

#########################
# format actions        #
#########################


def format_uppercase(value, regex):
    return value.upper()


def format_lowercase(value, regex):
    return value.lower()


def format_removeLast(value, regex):
    return value[:-1]


def format_removeFirst(value, regex):
    return value[1:]


def format_removeWhitespace(value, regex):
    return value.replace(' ', '')

def format_isniformat(value, regex):
    value = re.sub(r'[^0-9X]','', value)
    return value[0:4] + ' ' + value[4:8] + ' ' + value[8:12] + ' ' + value[12:16]


def format_dash(value, regex):
    return (value.encode('utf-8').replace('-', '–')).decode('utf-8')


def format_removePrefix(value, regex):
    for _ in range(0, len(value)):
        value = value[1:]
        if formatcheck(value, regex):
            return value
    return None


def format_removeSuffix(value, regex):
    for _ in range(0, len(value)):
        value = value[:-1]
        if formatcheck(value, regex):
            return value
    return None


def format_linkedin(value, regex):
    return re.sub('https?://(.*)linkedin.com/in/', 'https://www.linkedin.com/in/', value)


def format_isbn10(value, regex):
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

    res = re.findall(ur'<Prefix>978-'+country+'</Prefix>([^G]*)', f2)
    if not res:
        return None
    for m in res:
        res2 = re.findall(ur'<Range>([0-9]*)-([0-9]*)</Range><Length>([0-9])</Length>', m)
        if res2:
            for n in res2:
                if rest2 >= int(n[0]) and rest2 <= int(n[1]):
                    publisher = rest[0:int(n[2])]
                    work = rest[int(n[2]):-1]
                    return country+'-'+publisher+'-'+work+'-'+val[9]


#########################
# actions               #
#########################


def action_format(item, job):
    for claim in item.claims[job['p']]:
        if formatcheck(claim, job['regex']):
            continue
        subaction = globals()['format_' + job['subaction']]
        newVal = subaction(claim.getTarget(), job['regex'])
        if newVal:
            if formatcheck(newVal, job['regex']):
                claim.changeTarget(newVal)


def action_normalize(item, job):
    for claim in item.claims[job['p']]:
        m = claim.toJSON()
        curVal = m['mainsnak']['datavalue']['value']
        newVal = string.replace(curVal, '_', ' ')
        if newVal[0:5] == 'File:':
            newVal = newVal[5:]
        target = pywikibot.FilePage(siteCommons, newVal)
        if target.exists():
            claim.changeTarget(target)


#add an inverse claim
def action_inverse(item, job):
    #bug with checking for same claim
    for claim in item.claims[job['p']]:
        itemID = item.getID()
        target = claim.getTarget()
        if target.isRedirectPage():
            continue
        if not target.exists():
            continue
        target.get()
        if 'constrainttarget' in job:
            if not constraintTargetCheck(target, job):
                continue
        if target.claims:
            if job['pNewT'] in target.claims:
                for m in target.claims[job['pNewT']]:
                    if m.getTarget().getID() == itemID:
                        return 0
        claimNew = pywikibot.Claim(repo, job['pNewT'])
        claimNew.setTarget(item)
        target.addClaim(claimNew)


#move claim from pOld to pNew
def action_moveP(item, job):
    if not job['pOld'] in item.claims:
        return 0
    if job['pNew'] in item.claims:
        return 0
    data = item.toJSON()
    for m in data['claims'][job['pOld']]:
        mydata = {}
        mydata['claims'] = [{"id": m['id'], "remove":""}]
        m['mainsnak']['property'] = job['pNew']
        m.pop('id', None)
        mydata['claims'].append(m)
        item.editEntity(mydata, summary=u'move claim [[Property:'+job['pOld']+']] -> [[Property:'+job['pNew']+']]')


#move qualifiers on p from pOld to pNew
def action_moveQualifier(item, job):
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
        item.editEntity(mydata, summary=u'move qualifier [[Property:'+job['pOld']+']] -> [[Property:'+job['pNew']+']]')


#add claim pNew=valNew
def action_addClaim(item, job):
    if job['pNew'] in item.claims:
        return 0
    claimNew = pywikibot.Claim(repo, job['pNew'])
    itemNew = pywikibot.ItemPage(repo, job['valNew'])
    claimNew.setTarget(itemNew)
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


def action_changeClaim(item, job):
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
        summary = u'move claim [[Q' + str(curVal) + ']] -> [[Q' + str(newVal) + ']]'
        item.editEntity(mydata, summary=summary)


def action_removeUnit(item, job):
    for claim in item.claims[job['p']]:
        m = claim.toJSON()
        mydata = {}
        m['mainsnak']['datavalue']['value']['unit'] = '1'
        mydata['claims'] = [m]
        summary = u'remove unit'
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
    return 1


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


def check_item(item, constraint):
    if not constraint['p'] in item.claims:
        return False
    if 'val' in constraint:
        if isinstance(constraint['val'], basestring):
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


def formatcheck(claim, regex):
    if isinstance(claim, unicode):
        value = claim
    else:
        value = claim.getTarget()
    res = re.match('^'+regex+'$', value)
    if res:
        return True
    return False

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
    done = json.load(open('fixClaims/done.json'))
    jobs = json.load(open('fixClaims/jobs.json'))
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
    f1 = open('fixClaims/done.json', 'w')
    f1.write(json.dumps(done, ensure_ascii=False))


if __name__ == "__main__":
    main()
