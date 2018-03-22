#!/usr/bin/python

import sys, getopt, time, os, pymarc, glob

reload(sys)
sys.setdefaultencoding('utf-8')


def typeOfRecord(l06, l07, f008) :
	if l06 in "a,t" and l07 not in "b,i,s" : 
		if f008[23] in "q,s,o" : 	return 'Ebook'
		else : 				return 'Monograph'
	elif l06 in "a,t" and l07 in "b,i,s" :
		if f008[23] in "q,s,o" : 	return 'E-journal'
		else : 				return 'Serial'
	elif l06 in "m" : 			return 'Computer'
	elif l06 in "e,f" : 			return 'Map'
	elif l06 in "p" : 			return 'Mixed'
	elif l06 in "g,k,o,r" : 		return 'Visual'
	elif l06 in "c,d,i,j" : 		return 'Music'
	else :					return  'Unknown'

def printFieldAndRecordData(name, record, field, recordIndex) :
	template = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}"
	print template.format(
		name,
		record.leader,
		(record['001'] and record['001'].data) or (record['907'] and record['907']['a']),
		record['006'] and record['006'].data,
		record['007'] and record['007'].data,
		record['008'] and record['008'].data,
		field and field['a'],
		field and field.indicators[0],				                                 
		field and field.indicators[1],
		field and field.tag,
		field and field.subfields and repr([x.encode('utf-8') for x in field.subfields]),
		typeOfRecord(record.leader[6], record.leader[7], (record['008'] and record['008'].data)),
		record.title(),
		"Record_{}".format(recordIndex)		
		)

def printFieldsByCriteria(name,record, fieldsToPrint, recordIndex):	
	if fieldsToPrint :
		for field in fieldsToPrint:
			printFieldAndRecordData(name, record, field, recordIndex)
	else :
		printFieldAndRecordData(name, record, None, recordIndex)

from os import listdir
from os.path import isfile, join

records = 0
start = time.time()

files = glob.glob(sys.argv[1])[::-1]
bufsize = 0
logFile = open(sys.argv[2],"w",bufsize) 
logFile.write("{}".format(files))

for f in files:
	from pymarc import MARCReader
	with open(f, 'rb') as fh:
	    reader = MARCReader(fh,'rb')
	    for record in reader:
		records += 1
		if records % 1000 == 0 :
			elapsed = records/(time.time() - start)
			logFile.write("{}\t{}\t{}\n".format(elapsed, records,f))
		printFieldsByCriteria("696", record, record.get_fields('696'), records)
		printFieldsByCriteria("697", record, record.get_fields('697'), records)
		printFieldsByCriteria("698", record, record.get_fields('698'), records)
		printFieldsByCriteria("951", record, record.get_fields('951'), records)
logFile.write("{} records fetched in {} seconds".format(records, (time.time() - start)))
logFile.close() 
