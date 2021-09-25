#!/usr/bin/python
# -*- coding: UTF-8 -*-
#licensed under CC-Zero: https://creativecommons.org/publicdomain/zero/1.0

import pywikibot
import requests
import MySQLdb

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()

tasks = [
    {'language': 'cs',
    'site': 'cswiki',
    'project': 'wikipedia',
    'category': 'Wikipedie:Rozcestníky',
    'description': 'rozcestník na projektech Wikimedia'
    },
    {'language': 'da',
    'site': 'dawiki',
    'project': 'wikipedia',
    'category': 'Flertydig',
    'description': 'Wikimedia-flertydigside'
    },
    {'language': 'de',
    'site': 'dewiki',
    'project': 'wikipedia',
    'category': 'Begriffsklärung',
    'description': 'Wikimedia-Begriffsklärungsseite'
    },
    {'language': 'en',
     'site': 'enwiki',
     'project': 'wikipedia',
     'category': 'Disambiguation pages',
     'description': 'Wikimedia disambiguation page'
    },
    {'language': 'es',
     'site': 'eswiki',
     'project': 'wikipedia',
     'category': 'Wikipedia:Desambiguación',
     'description': 'página de desambiguación de Wikimedia'
    },
    {'language': 'fr',
    'site': 'frwiki',
    'project': 'wikipedia',
    'category': 'Homonymie',
    'description': 'page d\'homonymie de Wikimedia'
    },
    {'language': 'it',
    'site': 'itwiki',
    'project': 'wikipedia',
    'category': 'Pagine di disambiguazione',
    'description': 'pagina di disambiguazione di un progetto Wikimedia'
    },
    {'language': 'nl',
    'site': 'nlwiki',
    'project': 'wikipedia',
    'category': 'Wikipedia:Doorverwijspagina',
    'description': 'Wikimedia-doorverwijspagina'
    },
    {'language': 'pl',
    'site': 'plwiki',
    'project': 'wikipedia',
    'category': 'Strony ujednoznaczniające',
    'description': 'strona ujednoznaczniająca w projekcie Wikimedia'
    },
    {'language': 'pt',
    'site': 'ptwiki',
    'project': 'wikipedia',
    'category': 'Desambiguação',
    'description': 'página de desambiguação de um projeto da Wikimedia'
    },
    {'language': 'sv',
    'site': 'svwiki',
    'project': 'wikipedia',
    'category': 'Förgreningssidor',
    'description': 'Wikimedia-förgreningssida'
    }
]


def rb(term): #remove brackets with the word disambiguation page inside
    bracketterms = [u'desambiguação', u'desambiguación', u'disambigua', u'discretiva', u'gwahaniaethu', u'khu-pia̍t-ia̍h', u'kthjellim', u'maʼnolari', u'olika betydelser 2', u'pagklaro', u'razdvojba', u'razvrstavanje', u'reikšmės', u'razdvajanje', u'täpsustus', u'ujednoznacznienie', u'αποσαφήνιση', u'значения', u'搞清楚', u'동음이의',  u'այլ կիրառումներ', u'Суолталара', u'нысаниуджытæ', u'пояснение', u'значення', u'định hướng', u'ыҥ-влак', u'смустьтне', u'вишезначна одредница', u'rozlišovacia stránka', u'ابهام‌زدایی', u'توضيح', u'صفحات ابهام زدایی ویکی پدیا', u'andre betydninger', u'anlam ayrımı', u'argipena', u'halaman disambiguasi', u'apartigilo', u'laman nyahkekaburan', u'Wikimedia-förgreningssida', u'Wikimedia-Homonymiesäit', u'Wikipedia-pekerside', u'پەڕەی ڕوونکردنەوەی ویکیپیدیا', u'вишезначна одредница на Викимедији', u'página de desambiguação', u'razdvojbena stranica na Wikimediji', u'čvor stranica na Wikimediji', u'Laman nyahkekaburan', u'ବହୁବିକଳ୍ପ ପୃଷ୍ଠା', u'پەڕەی ڕوونکردنەوەی ویکیمیدیا', u'aðgreiningarsíða á Wikipediu', u'Halaman disambiguasi', u'Wikimedia-flertydigside', u'Wikimedia dubbelsinnigheidsblad', u'Wikipedia:Dubbelsinnigheid', u'Wikimedia:Pachina de desambigación', u'صفحة توضيح في ويكيميديا', u'ويكيبيديا:توضيح', u'توضيح', u'صفحة توضيح في ويكيبيديا', u'صفحة توضيح', u'ৱিকিপিডিয়া:দ্ব্যৰ্থতা দূৰীকৰণ', u'সহায়:দ্ব্যৰ্থতা দূৰীকৰণ', u'Wikipedia:Páxina de dixebra', u'Vikimediya:Dəqiqləşdirmə', u'Википедия:Күп мәғәнәлелек', u'Wikimedia:Begriffsklearung', u'пералік значэнняў у Вікіпедыі', u'неадназначнасць', u'аманімія', u'старонка значэнняў', u'disambiguation', u'Вікіпедыя:Неадназначнасць', u'старонка-неадназначнасьць у Вікіпэдыі', u'Пояснителна страница', u'пояснителна страница', u'Уикимедия пояснителна страница', u'উইকিপিডিয়া:দ্ব্যর্থতা নিরসন', u'Wikimedia:Disheñvelout', u'Wikimedia:Čvor', u'pàgina de desambiguació de Wikimedia', u'pàgina de desambiguació de Viquimèdia', u'Ajuda:Pàgina de desambiguació', u'Pàgina de desambiguació', u'Википеди:Цхьатера маьӀна дерш', u'Wikimedia:Mga pulong nga may labaw pa sa usa ka kahulogan', u'ڕوونکردنەوە', u'rozcestník', u'rozcestník na projektech Wikimedia', u'rozcestník', u'Sied för en mehrdüdig Begreep op Wikimedia', u'tudalen wahaniaethu Wikimedia', u'উইকিপিডিয়া দ্ব্যর্থতা নিরসন পাতা', u'Wikimedia:Flertydige titler', u'flertydig', u'Wikimedia-Begriffsklärungsseite', u'Begriffsklärung', u'Begriffsunterscheidung', u'Begriffsklärungsseite', u'BKL', u'BKS', u'Wegweiser', u'Wikipedia:Begriffsklärung', u'Wikimedia-Begriffsklärungsseite', u'Wikimedia-Begriffsklärungsseite', u'σελίδα αποσαφήνισης', u'Wikipedia-flertydigside', u'σελίδα αποσαφήνισης εγχειρημάτων Wikimedia', u'αποσαφήνιση λημμάτων', u'Wikimedia disambiguation page', u'Wikipedia:Disambiguation', u'Wikivoyage:Disambiguation', u'Disambiguation', u'DAB', u'Wikivoyage disambiguation', u'Disambiguation page', u'WMF disambiguation', u'Wikipedia disambiguation page', u'Help:Disambiguation', u'Wikipedia disambiguation page', u'Wikimedia disambiguation page', u'Vikimedia apartigilo', u'Wikimedia apartigilo', u'apartigilo', u'Helpo:Apartigiloj', u'página de desambiguación de Wikimedia', u'desambiguación de Wikimedia', u'desambiguación de Wikipedia', u'página de desambiguación de Wikipedia', u'página de desambiguación', u'Wikipedia:Disambiguation', u'pagina de desambiguacion de Wikimedia', u'Ayuda:Desambiguación', u'Wikimedia täpsustuslehekülg', u'Wikimedia:Argipen orri', u'صفحهٔ ابهام‌زدایی', u'täsmennyssivu', u'Wikimedia-täsmennyssivu', u'täsmennyssivu', u"page d'homonymie", u"page d'homonymie de Wikimedia", u"page d'homonymie d'un projet Wikimédia", u'homonymie', u'Aide:Homonymie', u'Muardüüdag artiikel', u'páxina de homónimos', u'páxina de homónimos de Wikimedia', u'Wikimedia:Homónimos', u'páxina de homónimos de Wikipedia', u'homónimos de Wikipedia', u'paxina de homonimos de Wikimedia', u'páxina de homónimos de Wikipedia', u'Axuda:Homónimos', u'Wikimedia-Begriffsklärigssite', u'વિકિપીડિયા:સંદિગ્ધ શીર્ષક', u'Wikipedia:Reddaghey', u'Vì-kî Mòi-thí seû-khì-ngi-ya̍p', u'ויקיפדיה:פירושונים', u'ויקיפדיה פירושונים', u'פירושונים ויקיפדיה', u'विकिपीडिया:बहुविकल्पी शब्द', u'सहायता:बहुविकल्पी', u'Wikimedija:Razdvojba', u'pismo', u'Wikipedija:Wjacezmyslnosć', u'Wikimédia-egyértelműsítőlap', u'egyértelműsítő lap', u'Վիքիմեդիայի նախագծի բազմիմաստության փարատման էջ', u'Wikimedia:Disambiguation', u'Wikimedia:Disambiguasi', u'laman disambiguasi', u'laman makna ganda', u'laman multiarti', u'Wikimedia:Panangilawlawag', u'Wikimedio:Homonimo', u'Wikimedia:Aðgreiningarsíður', u'pagina di disambiguazione di un progetto Wikimedia', u'pagina di disambiguazione', u'Aiuto:Disambiguazione', u'Aiuto:Omonimia', u'disambiguazione', u'ウィキメディアの曖昧さ回避ページ', u'曖昧さ回避', u'曖昧さ回避ページ', u'Wikimedia:Disambiguasi', u'ვიკიპედიის მრავალმნიშვნელობის გვერდი', u'Уикипедия:Айрық', u'ជំនួយ:អសង្ស័យកម្ម', u'ವಿಕಿಪೀಡಿಯ:ದ್ವಂದ್ವ ನಿವಾರಣೆ', u'위키미디어 동음이의어 문서', u'„Wat-eß-dat?“-Sigg en de Wikkipeidija', u'Wikipedia:Begriffsklärung', u'pagina discretiva', u'Wikimedia:Homonymie', u'Wikimedia:Verdudelikingspazjena', u'Vikimedija:Nuorodiniai straipsniai', u'Wikimedia projekta nozīmju atdalīšanas lapa', u'Wikimedia nozīmju atdalīšanas lapa', u'nozīmju atdalīšanas lapa', u'disambig', u'nozīmju atdalīšana', u'維基媒體釋義', u'Wikimedia:Disambiguasi', u'Википедиесь:Лама смусть', u'Викимедиина појаснителна страница', u'појаснителна страница', u'صفحة توضيح لويكيميديا', u'উইকিমিডিয়া দ্ব্যর্থতা নিরসন পাতা', u'یک صفحهٔ ابهام‌زدایی در ویکی‌پدیا', u'მრავალმნიშვნელოვანი', u'דף פירושונים', u'સ્પષ્ટતા પાનું', u'बहुविकल्पी पृष्ठ', u'Vikimēdijas nozīmju atdalīšanas lapa', u'വിക്കിപീഡിയ:വിവക്ഷകൾ', u'Wikimedia:Nyahkekaburan', u'Biquimédia:Zambiguaçon', u'ویکی پدیا:گجگجی بیتن', u"Wikimedia khu-pia̍t-ia̍h", u'Wikimedia-pekerside', u'hh-peker', u'Wikimedia:Mehrdüdig Begreep', u'deurverwiesziede', u'विकिपीडिया:बहुविकल्पी शब्द', u'Wikimedia-doorverwijspagina', u'Wikimedia doorverwijspagina', u'Wikimedia disambiguatiepagina', u'disambiguatiepagina', u'doorverwijspagina', u'dp', u'Help:Doorverwijspagina', u'Wikimedia-fleirtydingsside', u'Help:Frouque', u"pagina d'omonimia", u'Ajuda:Omonimia', u'ସହଯୋଗ:Disambiguation', u'Æххуыс:Нысаниуæгтæ', u'strona ujednoznaczniająca w projekcie Wikimedia', u'strona ujednoznaczniająca', u'página de desambiguação da Wikimedia', u'página de desambiguação da Wikimedia', u'Vikimidiya:Dudalipen', u'pagină de dezambiguizare Wikimedia', u'Wikimedia:Dezambiguizare', u'Help:Disambigua', u'страница значений в проекте Викимедиа', u'неоднозначность', u'disambiguation', u'Википедия:Неоднозначность', u'страница значений', u'омонимия', u'страница неоднозначности', u'Справка:Страницы разрешения неоднозначности', u'Справка:Неоднозначность', u'страница разрешения неоднозначности в проекте Викимедиа', u'pàggina di disambiguazzioni di Wikimedia', u'Aiutu:Disambiguazzioni', u'Wikimedia disambiguation page', u'Wikipedia:سلجھائپ', u'Wikimedia:Višeznačna odrednica', u'یک صفحهٔ ابهام‌زدایی ویکی‌مدیا', u'ウィキペディアの曖昧さ回避ページ', u'위키백과 동음이의어 문서', u'විකිපීඩියා:Disambiguation page', u'උදවු:අන්වක්‍රොතීකරණය', u'rozlišovacia stránka', u'Wikimédia:Rozlišovacia stránka', u'Wikimedija:Razločitev', u'Wikimedia:Kthjellime', u'вишезначна одредница на Википедији', u'Wikimedia:Bigriepskloorenge', u'Wikimedia:Disambiguasi', u'förgreningssida inom Wikimedia', u'Wikimedia:Särskiljning', u'grensida', u'gren', u'Sied för en mehrdüdig Begreep op Wikipedia', u'särskiljning', u'olika betydelser', u'strona ujednoznaczniająca Wikipedii', u'página de desambiguação de um projeto da Wikimedia', u'Wikimedia:Zajta ujednoznaczńajůnco', u'விக்கிப்பீடியா:பக்கவழி நெறிப்படுத்தல்', u'వికీపీడియా:అయోమయ నివృత్తి', u'หน้าแก้ความกำกวมวิกิมีเดีย', u'Wikimedia:Paglilinaw', u'Help:Disembigyuesen', u'Vikimedya anlam ayrımı sayfası', u'Википедия:Күп мәгънәле мәкаләләр', u'сторінка значень в проекті Вікімедіа', u'неоднозначність', u'ویکیپیڈیا:ضد ابہام', u'trang định hướng Wikimedia', u'Vükimed:Telplänov', u'Wikimedia:Omonimeye', u'װיקיפּעדיע:באדייטן', u'維基媒體搞清楚版', u'Wikimedia:Deurverwiespagina', u'消歧義', u'維基百科消歧義頁', u'維基媒體消歧義頁', u'维基媒体消歧义页', u'消歧义页', u'维基百科消歧义页', u'消歧義頁', u'消歧义', u'维基媒体消歧义页', u'维基媒体消歧义页', u'維基媒體消歧義頁', u'維基媒體消歧義頁', u'維基媒體消歧義頁', u'维基媒体消歧义页', u'维基媒体消歧义页', u'維基媒體消歧義頁', u'曖昧さ回避', u'동음이의']
    for t in bracketterms:
        term = term.replace('('+t+')', '').strip()
    return term

def isDisam(item):
    if 'P31' not in item.claims:
        return False
    for claim in item.claims['P31']:
        if claim.getTarget().getID() == 'Q4167410':
            return True
    return False

def main():
    db = MySQLdb.connect(host='wikidatawiki.analytics.db.svc.eqiad.wmflabs', db='wikidatawiki_p', read_default_file='~/replica.my.cnf')
    cur = db.cursor()
    db.set_character_set('utf8')
    cur.execute('SET NAMES utf8;')
    cur.execute('SET CHARACTER SET utf8;')
    cur.execute('SET character_set_connection=utf8;')

    for task in tasks:
        try:
            payload = {
                'language': task['language'],
                'project': task['project'],
                'categories': task['category'],
                'ns[0]': '1',
                'depth': '1',
                'show_redirects': 'no',
                'wikidata_item': 'without',
                'doit': '1',
                'format': 'json'
            }
            r = requests.get('http://petscan.wmflabs.org/', params=payload)
            data = r.json()
            for m in data['*'][0]['a']['*']:
                try:
                    title = rb(m['title'].replace('_', ' '))
                    query = 'SELECT DISTINCT wbit_item_id FROM wbt_item_terms JOIN wbt_term_in_lang ON wbit_term_in_lang_id = wbtl_id JOIN wbt_text_in_lang ON wbxl_id=wbtl_text_in_lang_id JOIN wbt_text ON wbx_id=wbxl_text_id WHERE wbtl_type_id=1 AND wbx_text="{:s}"'.format(title);
                    cur.execute(query)
                    cnt = {}
                    for row in cur.fetchall():
                        qid = 'Q'+str(row[0])
                        item = pywikibot.ItemPage(repo, qid)
                        item.get()
                        if isDisam(item):
                            cnt[qid] = 0
                            for sitelink in item.iterlinks():
                                if title == rb(sitelink.title()):
                                    cnt[qid] += 1
                    max = -1
                    maxarg = ''
                    for q in cnt:
                        if cnt[q] > max:
                            max = cnt[q]
                            maxarg = q
                    if maxarg != '':
                        item = pywikibot.ItemPage(repo, maxarg)
                        item.get()
                        if task['site'] not in item.sitelinks:
                            item.setSitelink({'site':task['site'], 'title':m['title']})
                    else:
                        data = {'sitelinks': {task['site']: {'site': task['site'], 'title': m['title']}} , 'labels':{task['language']:{'language':task['language'],'value': title}}, 'descriptions':{task['language']:{'language':task['language'],'value': task['description']}}, "claims":{"P31":[{"mainsnak":{"snaktype":"value","property":"P31","datavalue":{"value":{"entity-type":"item","id":"Q4167410"},"type":"wikibase-entityid"},"datatype":"wikibase-item"},"type":"statement","rank":"normal"}]}}
                        newitem = pywikibot.ItemPage(repo)
                        newitem.editEntity(data=data)
                except:
                    pass
        except:
            pass

if __name__ == "__main__":
    main()