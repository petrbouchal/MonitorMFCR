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
    csvout_druhove = "../output/VydajeDruhove" + '_' + filedatestring + '.csv'
    csvfile = open(csvout_druhove, 'wb')
    writer_druhove = csv.writer(csvfile, doublequote=True)

    csvdictfieldnames_druhove = ['orgyear', 'orgtype', 'orgid', 'orgchapter',
                                 'orgchaptername', 'zrizovatel',
                                 'rowid', 'rowname', 'rowlevel', 'rowparent', 'rozpocet',
                                 'pozmenach', 'skutecnost']
    writer_druhove.writerow(csvdictfieldnames_druhove)

    csvout_vysledovka = "../output/VydajeVysledovka" + '_' + filedatestring + '.csv'
    csvfile = open(csvout_vysledovka, 'wb')
    writer_vysledovka = csv.writer(csvfile, doublequote=True)

    csvdictfieldnames_vysledovka = ['orgyear', 'orgtype', 'orgid',
                                    'orgchapter', 'zrizovatel',
                                    'rowid', 'rowname', 'rowlevel', 'rowparent',
                                    'skutecnostLetos', 'skutecnostLoni']
    writer_vysledovka.writerow(csvdictfieldnames_vysledovka)

    csvout_availability = "../output/VydajeAvailability" + '_' + filedatestring + '.csv'
    csvfile = open(csvout_availability, 'wb')
    writer_availability = csv.writer(csvfile, doublequote=True)

    csvdictfieldnames_availability = ['year', 'type', 'id', 'chapter', 'chaptername',
                               'Druhove', 'availability']
    writer_availability.writerow(csvdictfieldnames_availability)

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
    for opt in opts:
        chapterdict = {'year' : yrurl['year'], 'id' : opt['value'],
                       'type' : 'chapter', 'chapter' : opt['value'],
                       'parentorg' : 'None', 'category' : 'None',
                       'orgname' : opt.contents[0], 'chaptername' : opt.contents[0],
                       'zrizovatel' : 'None'}
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
    orgtab = orgsoup.find('table', attrs={'id' : 'oss-table'})
    #print orgurl
    #print orgtab
    if orgtab != None:
        orgtab = orgtab.tbody
        orgrows = orgtab.find_all('tr')
        for orgrow in orgrows:
            orgcell_ICO = orgrow.find('td', attrs={'headers' : 'semi-ico'})
            orgcell_name = orgrow.find('td', attrs={'headers' : 'semi-name'})
            orgICO = orgcell_ICO.a.contents
            orgname = orgcell_name.a.contents
            #print orgICO[0]
            orgICOdict = {'year' : orgdict['year'], 'id' : orgICO[0],
                          'type' : 'OSS', 'chapternum' : orgdict['chapter'],
                          'parentorgICO' : 'None', 'parentorgname' : 'None',
                          'category' : 'None',
                          'orgname' : orgname[0], 'chaptername' : orgdict['orgname']}
            orgdicts.append(orgICOdict)
            #print(orgICOdict)


# SCRAPE DRUHOVE CLENENI

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
        org['availability'] = "Unavailable"
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
        csvrowdict_druhove = {
                   'year' : org['year'],
                   'orgtype' : org['type'],
                   'orgid' : org['id'],
                   'orgname' : org['orgname'],
                   'orgchapter' : org['chapter'],
                   'rowid' : rowid,
                   'rowname' : rowname,
                   'rowlevel' : level,
                   'rowparent' : parent,
                   'rozpocet' : rozpocet,
                   'pozmenach' : pozmenach,
                   'skutecnost' : skutecnost
                   }

        csvrow_druhove = [org['year'], org['type'], org['id'], org['chapter'],
                          org['chapternmae'], org['parentorgICO'], org['parentorgname'],
                          rowid, rowname, level, parent, rozpocet, pozmenach, skutecnost]
        if(writer_druhove.writerow(csvrow_druhove)):
            print("OK: Line (druhove) written.")
            org['availability'] = 'Available'

        csvrow_availability = [org['year'], org['type'], org['id'], org['chapter'], org['chaptername'],
                               'Druhove', org['availability']]
        writer_availability.writerow(csvrow_availability)

# CAPTURE ALL PRISPEVKOVE OF ALL ORGS

# Create list with all dicts that aren't chapters - chapters have no prispevkovky
ossdicts = []
for org in ossdicts:
    if org['orgtype'] != 'chapter':
        ossdicts.append(org)

for orgdict in ossdicts:
    sorgurl = urlbase + orgdict['year'] + urlmidjson_chapter + orgdict['id'] + '?do=loadContributoryOrganizations'
    #print orgurl
    sorgreq = urllib2.Request(orgurl, httpdata, httpheaders_json)
    sorgpage = urllib2.urlopen(orgreq).read()

    sorgpagehtml = json.loads(orgpage)['snippets']['snippet--contributoryOrgsSnippet']
    sorgsoup = BeautifulSoup(orgpagehtml)
    sorgtable = orgsoup.find('table', attrs={'class' : 'monitor-table clickable-table tablesorter'})
    if sorgtable == None:
        print("No prispevkovky for org " + orgdict['id'])
    else:
        sorgbody = sorgtable.tbody
        sorgrows = sorgbody.find_all('tr')
        for row in orgrows:
            sorgICO = row.find('td', attrs={'headers' : 'semi-ico'}).a.contents
            sorgname = row.find('td', attrs={'headers' : 'semi-name'}).a.contents
            sorgtype = row.find('td', attrs={'headers' : 'semi-cofog'}).a.contents
            sorgdict = {'year' : orgdict['year'], 'id' : sorgICO[0],
                          'type' : 'PO', 'chapternum' : orgdict['chapter'],
                          'parentorgICO' : orgdict['id'], 'parentorgname' : orgdict['orgname'],
                          'category' : sorgtype[0],
                          'orgname' : sorgname[0], 'chaptername' : orgdict['chaptername']}
            orgdicts.append(sorgdict)



# SCRAPE ALL VYSLEDOVKY FOR ALL ORGS
# TODO: SCRAPE VYSLEDOVKY FOR ALL ORGS

tail = '?do=loadIncomeStatement'
for org in orgdicts:
    if org['type'] == 'chapter': continue
    if org['type'] == 'OSS': urlmidjson = '/statni-rozpocet/oss-sf/'
    if org['type'] == 'PO': urlmidjson = '/prispevkove-organizace/detail/'
    isurl = urlbase + org['year'] + urlmidjson + org['id'] + tail
    isreq = urllib2.Request(isurl, httpdata, httpheaders_json)
    ispage = urllib2.urlopen(isreq).read()
    ispagehtml = json.loads(ispage)['snippets']['snippet--incomeStatementSnippet']
    issoup = BeautifulSoup(ispagehtml)

