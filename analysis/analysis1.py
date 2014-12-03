# run as batch script

import gzip, csv, os
import ast
import numpy as np


import re
pattern = re.compile("([^,]*),(\d*),[^\[]*(\[.*\])[^\]]*")



def tryfunc(xfunc, xs,  valOnException=None):
    '''
    Tries a function and returns valOnException on exception
    '''
    try:
        return xfunc(xs)
    except:
        return valOnException

def mean(x):
    if x:
        return np.average(x)
    else:
        return None


#This funciton calculates all summary Stats
def summaryDictionary(allJournals):
    '''
    FFA: first first-author year:  1879.0
    FLA: first last-author year:  1968.0
    LAA: last all-author year:  1998.0
    TFA: total first author paper:  28
    TLA: total last author paper:  6
    TAA: total paper (all author):  41
    TCL: total career legth =  LAA - FFA:  119.0
    FCL: faculty career length = LAA - FLA:  30.0
    SCL: non-faculty scientist career length = TLA-FCL:  1849.0
    TCL2: total career length = SCL + FCL:  1879.0
    FRQFA: frequency of first author = TFA/SCL:  0.0151433207139
    FRQTA: frequency of all authorship = TAA/TCL:  0.344537815126
    FAEF: average first-author eigenfactor
    MAEF: average middle-author eigenfactor
    LAEF: average last-author eigenfactor
    '''

    pubsummary = []
    for entry in allJournals:
        dictEn = dict(entry)
        year = dictEn['year']
        if year:
            year = float(year)        
        isFirstAuthor = dictEn['authPos'] == 1
        isLastAuthor  = dictEn['authPos'] == dictEn['authCount']
        nlmuniqueid   = dictEn['nlmuniqueid']
        affiliation   = dictEn['affiliation']
        try:
            ef = eigenfactordict[nlmuniqueid]
        except:
            ef = None
        
        pubsummary.append(dict(year=year,isFirstAuthor=isFirstAuthor, isLastAuthor=isLastAuthor, ef = ef, affiliation = affiliation))
        
    taap_total_paper              = len(pubsummary)
    tfap_total_first_author_paper = len([x for x in pubsummary if x['isFirstAuthor']])
    tlap_total_last_author_paper  = len([x for x in pubsummary if x['isLastAuthor']])
    
    # filter for publication with actual years
    pubsummary_years = [x for x in pubsummary if x['year']]
    
    laay_last_all_author_paper_year    = tryfunc(max, [x['year'] for x in pubsummary_years])
    ffay_first_first_author_paper_year = tryfunc(min, [x['year'] for x in pubsummary_years if x['isFirstAuthor']])
    flay_first_last_author_paper_year  = tryfunc(max, [x['year'] for x in pubsummary_years if x['isLastAuthor']])
    
    
    # average first author EF 
    faef_first_author_ef = mean([x['ef'] for x in pubsummary if x['isFirstAuthor'] and x['ef']])
    # average middle author EF
    maef_middle_author_ef = mean([x['ef'] for x in pubsummary if not x['isFirstAuthor'] and not x['isLastAuthor'] and x['ef']])
    # average last author EF
    laef_middle_author_ef = mean([x['ef'] for x in pubsummary if x['isLastAuthor'] and x['ef']])
    # scientist (non-last author) ef
    saef_all_author_ef = mean([x['ef'] for x in pubsummary if not x['isLastAuthor'] and x['ef']])
    
    # get list of affiliations for last-author papers
    zaffs = ','.join(['"""%s"""'%x['affiliation'] for x in pubsummary if x['affiliation'] and x['isLastAuthor']])
    
    
    # total caeer length (tcl = laay - ffay)
    if laay_last_all_author_paper_year and ffay_first_first_author_paper_year:
        tcl_total_career_length = laay_last_all_author_paper_year - ffay_first_first_author_paper_year
    else:
        tcl_total_career_length = 0

    # faculty caeer length (fcl = laay - flay)
    if laay_last_all_author_paper_year and flay_first_last_author_paper_year:
        fcl_faculty_career_length = laay_last_all_author_paper_year - flay_first_last_author_paper_year
    else:
        fcl_faculty_career_length = 0
    
    # scientist career length
    scl_scientist_career_length = tcl_total_career_length - fcl_faculty_career_length
    
    
    #Can't divide by 0, so force the career length minimum to 1 year, (which is reasonable)
    #change defaults here if they are not changed from above
    if scl_scientist_career_length == 0:
        scl_scientist_career_length = 1
    if tcl_total_career_length == 0:
        tcl_total_career_length = 1
    
    summary = dict(
            ffay   = ffay_first_first_author_paper_year,
            flay   = flay_first_last_author_paper_year,
            laay   = laay_last_all_author_paper_year,
            tfap   = tfap_total_first_author_paper,
            tlap   = tlap_total_last_author_paper,
            taap   = taap_total_paper,
            tcl   = tcl_total_career_length,
            fcl   = fcl_faculty_career_length,
            scl   = scl_scientist_career_length,
            frqfa = tfap_total_first_author_paper/scl_scientist_career_length,
            frqta = taap_total_paper/tcl_total_career_length,
            faef  = faef_first_author_ef,
            maef  = maef_middle_author_ef,
            laef  = laef_middle_author_ef,
            saef  = saef_all_author_ef,
            zaffs = zaffs,
        )
    return summary



# get eigenfactor table
eigenfactordict = {}
reader = csv.reader(open("eigenfactor.csv", 'r'), dialect=csv.excel)
eigenfactordict = dict( [ (nlmuniqueid, tryfunc(float, ef))  for idx, ai, ef, issn, journal, nlmuniqueid, rank in reader if nlmuniqueid and tryfunc(float, ef)  ])
    

infileLocation = "filtered2.txt.zip"

outfile = gzip.open("authorStat.txt.zip", 'w')




# answer = []
for idx, rawrow in enumerate(gzip.open( infileLocation, 'r'), start=1): #reader:
#     if idx == 10000: break # limit for testing
    if idx%10000 == 0:
        print idx
        
    try:
        author, _, raw_articles = pattern.findall(rawrow)[0]
        sumData = summaryDictionary(ast.literal_eval(raw_articles))
        sumData["author"] = author
        if idx == 1: # write header
            outfile.write("%s\n"%(",".join(sumData.keys())))
        if sumData['taap'] > 1 and sumData['tfap'] > 0 and sumData['scl'] > 0:
            #answer.append(sumData)
            outfile.write("%s\n"%(",".join(sumData.values())))
    except:
        print "error in index %d with author %s"%(idx, rawrow.split(',')[0])

outfile.close()

