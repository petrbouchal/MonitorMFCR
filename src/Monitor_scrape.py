'''
Created on May 1, 2013

@author: petrbouchal
'''
import urllib2
import urllib
import csv
import json
from bs4 import BeautifulSoup
from datetime import datetime

# SELECT YEARS, SCOPE OF DATA AND ORGS, AND STORAGE TYPES

#years = ['2012']
years = ['2010', '2011', '2012']

writecsv = 1

collectbudget = 1
collectvysledovky = 1

includeoss = 1
includeprispevkovky = 1

# SET UP CONSTANT BITS

now = datetime.now()
today = datetime.today()

# build date and time strings
datestring = datetime.strftime(today, '%Y-%m-%d')
datetimestring = datetime.strftime(now, '%Y-%m-%d%H:% M:%S')
filedatestring = datetime.strftime(now, '%Y%m%d_%H%M')
filedatestringlong = datetime.strftime(now, '%Y%m%d_%H%M%S')


urlbase = 'http://monitor.statnipokladna.cz/'

urlmidjson_chapter = '/statni-rozpocet/kapitola/'
urlmidjson_ico = '/statni-rozpocet/oss-sf/'

httpdata = None
httpheaders_json = {
               'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.65 Safari/537.36',
               'Host' : 'monitor.statnipokladna.cz',
               'Connection' : 'keep-alive',
               'Cache-Control' : 'max-age=0',
               'Accept' : 'application/json, text/javascript, */*; q=0.01',
               'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8',
               'Origin' : 'http://monitor.statnipokladna.cz',
               'Accept-Encoding':'gzip,deflate,sdch',
               'Accept-Language':'cs,en-US;q=0.8,en;q=0.6,de;q=0.4',
               'X-Requested-With' : 'XMLHttpRequest',
               "Cookie" : "monitor-radix=C"
               }

httpheaders_html = {
               'Host': 'monitor.statnipokladna.cz',
               'Connection': 'keep-alive',
               'Cache-Control': 'max-age=0',
               'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9,*/* ;q=0.8',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.65 Safari/537.36',
               'Accept-Encoding': 'gzip,deflate,sdch',
               'Accept-Language': 'cs,en-US;q=0.8,en;q=0.6,de;q=0.4'
              }

# SET UP CSV
if writecsv == 1:
    if collectbudget == 1:
        csvout_druhove = "../output/VydajeDruhove" + '_' + filedatestring + '.csv'
        csvfile_druhove = open(csvout_druhove, 'wb')
        writer_druhove = csv.writer(csvfile_druhove, doublequote=True)

        csvdictfieldnames_druhove = ['orgyear', 'orgtype', 'orgid', 'orgname',
                                     'orgchapter',
                                     'orgchaptername', 'zrizovatel', 'category',
                                     'rowid', 'rowname', 'rowlevel', 'rowparent',
                                     'rozpocet', 'pozmenach', 'skutecnost']
        writer_druhove.writerow(csvdictfieldnames_druhove)

    if collectvysledovky == 1:
        csvout_vysledovka = "../output/VydajeVysledovka" + '_' + filedatestring + '.csv'
        csvfile_vysledovka = open(csvout_vysledovka, 'wb')
        writer_vysledovka = csv.writer(csvfile_vysledovka, doublequote=True)

        csvdictfieldnames_vysledovka = ['year', 'orgid', 'orgname', 'chapternum',
                       'chaptername', 'parentorgICO', 'parentorgname', 'type',
                       'category', 'vysltype', 'itemcode', 'itemname', 'synaccount',
                       'rownum',
                       'beznehlavni', 'beznehospodarska',
                       'minulehlavni', 'minulehospodarska']
        writer_vysledovka.writerow(csvdictfieldnames_vysledovka)

    csvout_availability = "../output/VydajeAvailability" + '_' + filedatestring + '.csv'
    csvfile_availability = open(csvout_availability, 'wb')
    writer_availability = csv.writer(csvfile_availability, doublequote=True)

    csvdictfieldnames_availability = ['year', 'type', 'id', 'chapter',
                                      'chaptername', 'orgname',
                                      'datatype', 'availability']
    writer_availability.writerow(csvdictfieldnames_availability)

# CAPTURE ALL CHAPTER NUMBERS FOR EACH YEAR

yrurls = []
for year in years:
    urldict = {'year' : year, 'url' : 'http://monitor.statnipokladna.cz/'
               + year + '/statni-rozpocet/'}
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
                       'type' : 'chapter', 'chapternum' : opt['value'],
                       'parentorgname' : 'None', 'category' : 'None',
                       'orgname' : opt.contents[0], 'chaptername' : opt.contents[0],
                       'parentorgICO' : 'None'}
        if len(chapterdict['chapternum']) != 0:
            orgdicts.append(chapterdict)

#for i in orgdicts: print i
print('Found ' + str(len(orgdicts)) + ' budget chapters over ' +
      str(len(years)) + ' years.')

# CAPTURE ALL SUBORDINATE ORGS FOR EACH CHAPTER
if includeoss == 1: print('Getting list of organisations')
chapterdicts = orgdicts[:]
for orgdict in chapterdicts:
    if includeoss != 1: break
    orgurl = (urlbase + orgdict['year'] + urlmidjson_chapter + orgdict['id'] +
              '?do=loadGovernmentDepartments')
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
                          'type' : 'OSS', 'chapternum' : orgdict['chapternum'],
                          'parentorgICO' : 'None', 'parentorgname' : 'None',
                          'category' : 'None',
                          'orgname' : orgname[0], 'chaptername' : orgdict['orgname']}
            orgdicts.append(orgICOdict)
            #print(orgICOdict)

print('Found ' + str(len(orgdicts)) + ' budget chapters and orgs over ' +
      str(len(years)) + ' years.')

# SCRAPE DRUHOVE CLENENI [BUDGET DATA]

tail_chapter = '?do=loadChapterOutgoingsBudgetByItems'
tail_ico = '?do=loadGovernmentDepartmentOutgoingsBudgetByItems'

for org in orgdicts:
    if collectbudget != 1: break
    if org['type'] == 'chapter':
        url = urlbase + org['year'] + urlmidjson_chapter + org['id'] + tail_chapter
    elif org['type'] == 'OSS':
        url = urlbase + org['year'] + urlmidjson_ico + org['id'] + tail_ico
    print url
    httpdata = urllib.urlencode({"ico" : org['id']})
    req = urllib2.Request(url, httpdata, httpheaders_json)
    try:
        datajson = urllib2.urlopen(req)
    except IOError:
        try:
            datajson = urllib2.urlopen(req)
        except IOError:
            print("Error reading URL on " + org['id'] +
                  '. Continuing to next organisation.')
            continue
    datajson = datajson.read()
    data = json.loads(datajson)
    html = data['snippets']['snippet--outgoingsBudgetByItemsSnippet']
    soup = BeautifulSoup(html)
    #print soup
    errorpage = soup.find('p', attrs={'class' : 'empty-result'})
    if errorpage != None:
        print org['id'] + ': No budget data for this organisation ' + 'in ' + org['year']
        availability = "Unavailable"
        csvrow_availability = [org['year'], org['type'], org['id'], org['chapternum'],
                               org['chaptername'], org['orgname'], 'Druhove', availability]
        if writecsv == 1: writer_availability.writerow(csvrow_availability)
        continue
    table = soup.tbody
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
        rozpocet = figures[0].contents[0].replace(' ', '')
        pozmenach = figures[1].contents[0].replace(' ', '')
        skutecnost = figures[2].contents[0].replace(' ', '')
        csvrow_druhove = [org['year'], org['type'], org['id'], org['orgname'],
                          org['chapternum'], org['chaptername'], org['parentorgICO'],
                          org['parentorgname'],
                          rowid, rowname, level, parent, rozpocet, pozmenach, skutecnost]
        if writecsv == 1:  writer_druhove.writerow(csvrow_druhove)
        #print csvrow_druhove

    availability = 'Available'
    csvrow_availability = [org['year'], org['type'], org['id'], org['chapternum'],
                           org['chaptername'], org['orgname'], 'Druhove', availability]
    if writecsv == 1: writer_availability.writerow(csvrow_availability)
    #print csvrow_availability
if writecsv == 1 & collectbudget == 1: csvfile_druhove.close()

# CAPTURE ALL PRISPEVKOVE ORGs OF ALL ORGS

# Create list with all dicts that aren't chapters - chapters have no prispevkovky
prispevkovkycount = 0
ossdicts = []
if includeprispevkovky == 1: print('Collecting POs')
for org in orgdicts:
    if org['type'] != 'chapter':
        ossdicts.append(org)

tail = '?do=loadContributoryOrganizations'
for orgdict in ossdicts:
    #FIXME: this cycle doesn't return anything
    if includeprispevkovky != 1: break
    sorgurl = urlbase + orgdict['year'] + urlmidjson_ico + orgdict['id'] + tail
    print sorgurl
    httpdata = urllib.urlencode({"ico" : orgdict['id']})
    sorgreq = urllib2.Request(sorgurl, httpdata, httpheaders_json)
    sorgpage = urllib2.urlopen(sorgreq).read()

    sorgpagehtml = json.loads(sorgpage)['snippets']['snippet--contributoryOrgsSnippet']
    sorgsoup = BeautifulSoup(sorgpagehtml)
    #print sorgsoup
    sorgtable = sorgsoup.find('table', attrs={'id' : 'semi-budgetary-org'})
    if sorgtable == None:
        print("No prispevkovky for org " + orgdict['id'])
        continue
    else:
        sorgbody = sorgtable.tbody
        sorgrows = sorgbody.find_all('tr')
        for row in sorgrows:
            sorgICO = row.find('td', attrs={'headers' : 'semi-ico'}).a.contents
            sorgname = row.find('td', attrs={'headers' : 'semi-name'}).a.contents
            sorgtype = row.find('td', attrs={'headers' : 'semi-cofog'}).a.contents
            sorgdict = {'year' : orgdict['year'], 'id' : sorgICO[0],
                          'type' : 'PO', 'chapternum' : orgdict['chapternum'],
                          'parentorgICO' : orgdict['id'],
                          'parentorgname' : orgdict['orgname'],
                          'category' : sorgtype[0],
                          'orgname' : sorgname[0],
                          'chaptername' : orgdict['chaptername']}
            orgdicts.append(sorgdict)
            prispevkovkycount += 1

print('Found ' + str(prispevkovkycount) + ' prispevkovky over ' +
      str(len(years)) + ' years.')
print('Number of orgs in list total over all years: ' + str(len(orgdicts)))


# SCRAPE ALL VYSLEDOVKY FOR ALL ORGS [INCOME/EXPENDITURE STATEMENTS]
# note budget data is not scraped for all, only for chapters and orgs, not for
# prispevkovky
# TODO: SCRAPE VYSLEDOVKY FOR ALL ORGS

if collectvysledovky == 1:
    tail = '?do=loadIncomeStatement'
    print 'Collecting income statements for', len(orgdicts), 'organisations.'
for org in orgdicts:
    if collectvysledovky != 1: break
    if org['type'] == 'chapter': continue
    if org['type'] == 'OSS': urlmidjson = '/statni-rozpocet/oss-sf/'
    if org['type'] == 'PO': urlmidjson = '/prispevkove-organizace/detail/'
    isurl = urlbase + org['year'] + urlmidjson + org['id'] + tail
    print isurl
    httpdata = urllib.urlencode({"ico" : org['id']})
    isreq = urllib2.Request(isurl, httpdata, httpheaders_json)
    ispage = urllib2.urlopen(isreq).read()
    ispagehtml = json.loads(ispage)['snippets']['snippet--incomeStatementSnippet']
    issoup = BeautifulSoup(ispagehtml)
    #print issoup
    if issoup.find('p', attrs={'class' : 'empty-result'}) != None:
        availability = 'Unavailable'
        csvrow_availability = [org['year'], org['type'], org['id'], org['chapternum'],
                               org['chaptername'], org['orgname'], 'Vysledovka', availability]
        if writecsv == 1: writer_availability.writerow(csvrow_availability)
        print('No vysledkovka available for ' + org['id'] + ' in ' + org['year'])
        continue
#    print(issoup)
    availability = 'Available'
    csvrow_availability = [org['year'], org['type'], org['id'], org['chapternum'],
                           org['chaptername'], org['orgname'], 'Vysledovka', availability]
    if writecsv == 1: writer_availability.writerow(csvrow_availability)
    exptab = issoup.find('table', attrs={'id' : 'expenses'}).tbody
    revtab = issoup.find('table', attrs={'id' : 'revenues'}).tbody
    # create list of two dicts, marked expenditures and revenues, with data as content
    vysltabs = [{"type" : "expenditures", "data" : exptab.find_all('tr')},
                 {"type" : "revenues", "data" : revtab.find_all('tr')}]
    # iterate through divts - this helps avoid duplication of work as the two 
    # parts of the statement are structurally identical
    for vysltab in vysltabs:
        vysltype = vysltab['type']
        #print vysltab['data']
        vyslrows = vysltab['data']
        for row in vyslrows:
            cells = row.find_all('td')
            itemcode = cells[0].contents[0]
            itemname = cells[1].contents[0]
            synaccount = cells[2].contents[0]
            rownum = cells[3].contents[0]
            beznehlavni = cells[4].contents[0].replace(' ', '')
            beznehospodarska = cells[5].contents[0].replace(' ', '')
            minulehlavni = cells[6].contents[0].replace(' ', '')
            minulehospodarska = cells[7].contents[0].replace(' ', '')
            csvrow_vysl = [org['year'], org['id'], org['orgname'], org['chapternum'],
                           org['chaptername'], org['parentorgICO'],
                           org['parentorgname'], org['type'],
                           org['category'],
                           vysltype, itemcode, itemname, synaccount, rownum,
                           beznehlavni, beznehospodarska,
                           minulehlavni, minulehospodarska]
            if writecsv == 1: writer_vysledovka.writerow(csvrow_vysl)
if writecsv == 1:
    if collectvysledovky == 1: csvfile_vysledovka.close()
    csvfile_availability.close()
