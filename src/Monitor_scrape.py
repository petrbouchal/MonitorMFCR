'''
Created on May 1, 2013

@author: petrbouchal
'''
import urllib2
import csv
import json
from bs4 import BeautifulSoup
from datetime import datetime

# SELECT YEARS AND STORAGE TYPES

years = ['2010', '2011', '2012']
writecsv = 1

# SET UP CONSTANT BITS

now = datetime.now()
today = datetime.today()

# build date and time strings
datestring = datetime.strftime(today, '%Y-%m-%d')
datetimestring = datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
filedatestring = datetime.strftime(now, '%Y%m%d_%H%M')
filedatestringlong = datetime.strftime(now, '%Y%m%d_%H%M%S')


urlbase = 'http://monitor.statnipokladna.cz/'

urlmidjson_chapter = '/statni-rozpocet/kapitola/'
urlmidjson_ico = '/statni-rozpocet/oss-sf/'
urltailjson_chapter = '?do=loadChapterOutgoingsBudgetByItems'
urltailjson_ico = '?do=loadGovernmentDepartmentOutgoingsBudgetByItems'


httpdata = None
httpheaders_json = {
               'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.65 Safari/537.36',
               'Host' : 'monitor.statnipokladna.cz',
               'Connection' : 'keep-alive',
               'Cache-Control' : 'max-age=0',
               'Accept' : 'application/json, text/javascript, */*; q=0.01',
               'Conent-Type' : 'Content-Type:application/x-www-form-urlencoded; charset=UTF-8',
               'Origin' : 'http://monitor.statnipokladna.cz',
               'Accept-Encoding' : 'gzip,deflate,sdch',
               'Accept-Language' : 'cs,en-US;q=0.8,en;q=0.6,de;q=0.4',
               'X-Requested-With' : 'XMLHttpRequest'
               }

httpheaders_html = {
               'Host': 'monitor.statnipokladna.cz',
               'Connection': 'keep-alive',
               'Cache-Control': 'max-age=0',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.65 Safari/537.36',
               'Accept-Encoding': 'gzip,deflate,sdch',
               'Accept-Language': 'cs,en-US;q=0.8,en;q=0.6,de;q=0.4'
              }

# SET UP CSV
if writecsv == 1:
    csvout = "../output/VydajeDruhove" + '_' + filedatestring + '.csv'
    csvout_final = '../output/BusinessPlans_current.csv'
    csvfile = open(csvout, 'wb')
    writer = csv.writer(csvfile, doublequote=True)

csvdictfieldnames = ['orgyear', 'orgtype', 'orgid', 'orgchapter', 'rowid', 'rowname',
                     'rowlevel', 'rowparent', 'rozpocet', 'pozmenach', 'skutecnost']
writer.writerow(csvdictfieldnames)

# CAPTURE ALL CHAPTER NUMBERS FOR EACH YEAR

yrurls = []
for year in years:
    urldict = {'year' : year, 'url' : 'http://monitor.statnipokladna.cz/' + year + '/statni-rozpocet/'}
    yrurls.append(urldict)

#print yrurls
print("Getting list of budget chapters")
orgdicts = []
for yrurl in yrurls:
    #print yrurl
    req_yr = urllib2.Request(yrurl['url'], httpdata, httpheaders_html)
    data = urllib2.urlopen(req_yr).read()
    yrsoup = BeautifulSoup(data)
    select = yrsoup.find('select', attrs={'id' : 'chapter', 'name': 'chapter'})
    opts = select.find_all('option')
    #TODO: pickup the names too and either save in sep table or keep in dict+csv
    for opt in opts:
        chapterdict = {'year' : yrurl['year'], 'id' : opt['value'],
                       'type' : 'chapter', 'chapter' : opt['value'],
                       'parentorg' : 'None', 'category' : 'None',
                       'orgname' : 'TBDone'}
        if len(chapterdict['chapter']) != 0:
            orgdicts.append(chapterdict)

#for i in orgdicts: print i

# CAPTURE ALL SUBORDINATE ORGS FOR EACH CHAPTER
print('Getting list of organisations')
chapterdicts = orgdicts[:]
for orgdict in chapterdicts:
    orgurl = urlbase + orgdict['year'] + urlmidjson_chapter + orgdict['id'] + '?do=loadGovernmentDepartments'
    #print orgurl
    orgreq = urllib2.Request(orgurl, httpdata, httpheaders_json)
    orgpage = urllib2.urlopen(orgreq).read()
    orgpagehtml = json.loads(orgpage)['snippets']['snippet--governmentDepartmentsSnippet']
    orgsoup = BeautifulSoup(orgpagehtml)
    #TODO: pick up the name too and keep in dict + write to CSV
    orgtab = orgsoup.find('table', attrs={'id' : 'oss-table'})
    if orgtab != None:
        orgrows = orgtab.find_all('td', attrs={'headers' : 'semi-ico'})
        for orgrow in orgrows:
            orgICO = orgrow.a.contents
            #print orgICO[0]
            orgICOdict = {'year' : orgdict['year'], 'id' : orgICO[0],
                          'type' : 'OSS', 'chapter' : orgdict['chapter'],
                          'parentorg' : 'None', 'category' : 'None',
                          'orgname' : 'TBDone'}
            orgdicts.append(orgICOdict)
            #print(orgICOdict)

# CAPTURE ALL PRISPEVKOVE OF ALL ORGS
#TODO: CAPTURE ALL PRISPEVKOVKY FOR EACH ORG (use new item in orgdict to capture zrizovatel)
#TODO: When capturing prispevkovky, capture name and category too

# SCRAPE DRUHOVE CLENENI
# TODO: MAKE CSV capturing data availability (statementtype, orgID, chapter, name, year, available)

for org in orgdicts:
    if org['type'] == 'chapter':
        url = urlbase + org['year'] + urlmidjson_chapter + org['id'] + urltailjson_chapter
    elif org['type'] == 'OSS':
        url = urlbase + org['year'] + urlmidjson_ico + org['id'] + urltailjson_ico
    print url
    req = urllib2.Request(url, httpdata, httpheaders_json)
    try:
        datajson = urllib2.urlopen(req)
    except IOError:
        try:
            datajson = urllib2.urlopen(req)
        except IOError:
            print("Error reading URL on " + org['id'] + '. Continuing to next organisation.')
            continue
    datajson = datajson.read()
    data = json.loads(datajson)
    html = data['snippets']['snippet--outgoingsBudgetByItemsSnippet']
    #print(html)
    soup = BeautifulSoup(html)
    errorpage = soup.find('p', attrs={'class' : 'empty-result'})
    if errorpage != None:
        print org['id'] + ": No data for this organisation"
        continue
    table = soup.find('tbody')
    rows = table.find_all('tr')
    for row in rows:
        #print row
        rowid = row['data-tt-id']
        rowname = row.th.contents[0]
        figures = row.find_all('td')
        if rowid != "0":
            level = row['class'][0]
            parent = row['data-tt-parent-id']
        else:
            level = '0'
            parent = 'None'
        #print rowname, level, rowid, parent
        rozpocet = figures[0].contents[0].replace(' ', '')
        pozmenach = figures[1].contents[0].replace(' ', '')
        skutecnost = figures[2].contents[0].replace(' ', '')
        #print rowname, rozpocet, pozmenach, skutecnost
        csvrowdict = {
                   'year' : org['year'],
                   'orgtype' : org['type'],
                   'orgid' : org['id'],
                   'orgchapter' : org['chapter'],
                   'rowid' : rowid,
                   'rowname' : rowname,
                   'rowlevel' : level,
                   'rowparent' : parent,
                   'rozpocet' : rozpocet,
                   'pozmenach' : pozmenach,
                   'skutecnost' : skutecnost
                   }

        csvrow = [org['year'], org['type'], org['id'], org['chapter'], rowid, rowname,
                  level, parent, rozpocet, pozmenach, skutecnost]
        if(writer.writerow(csvrow)):
            print("OK: Line written.")

# SCRAPE ALL VYSLEDOVKY FOR ALL ORGS
# TODO: SCRAPE VYSLEDOVKY FOR ALL ORGS 
