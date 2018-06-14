import sys
import time
import pymarc
import glob

# No need in python3, right?
# reload(sys)
# sys.setdefaultencoding('utf-8')


def type_of_record(l06, l07, f008):
    if l06 in "a,t" and l07 not in "b,i,s":
        if f008[23] in "q,s,o":
            return 'Ebook'
        else:
            return 'Monograph'
    elif l06 in "a,t" and l07 in "b,i,s":
        if f008[23] in "q,s,o":
            return 'E-journal'
        else:
            return 'Serial'
    elif l06 in "m":
        return 'Computer'
    elif l06 in "e,f":
        return 'Map'
    elif l06 in "p":
        return 'Mixed'
    elif l06 in "g,k,o,r":
        return 'Visual'
    elif l06 in "c,d,i,j":
        return 'Music'
    else:
        return 'Unknown'


def print_field_and_record_data(name, record, field, record_index):
    print(name + '\t' + record.leader + '\t' +
          (record['001'] and record['001'].dat) + '\t' +
          (record['006'] and record['006'].data) + '\t' +
          (record['007'] and record['007'].data) + '\t' +
          (record['008'] and record['008'].data) + '\t' +
          (field and field['a']) + '\t' +
          (field and field.indicators[0]) + '\t' +
          (field and field.indicators[1]) + '\t' +
          (field and field.tag) + '\t' +
          (field and field.subfields and repr([x.encode('utf-8') for x in field.subfields])) + '\t' +
          (type_of_record(record.leader[6], record.leader[7], (record['008'] and record['008'].data))) + '\t' +
          (record.title()) + '\t' +
          ("Record_{}".format(record_index)) + '\t' +
          (field and field['z']) + '\t' +
          (record['907'] and record['907']['a']) + '\t' +
          (record['907'] and record['907']['b']) + '\t')


def print_fields_by_criteria(name, record, fields_to_print, record_index):
    if fields_to_print:
        for field in fields_to_print:
            print_field_and_record_data(name, record, field, record_index)
    else:
        print_field_and_record_data(name, record, None, record_index)


i = 0
start = time.time()

files = glob.glob(sys.argv[1])[::-1]
bufsize = 0
logFile = open(sys.argv[2], "w", bufsize)
logFile.write("{}".format(files))

for f in files:
    from pymarc import MARCReader
    with open(f, 'rb') as fh:
        reader = MARCReader(fh, 'rb')
        for rec in reader:
            i += 1
            if i % 1000 == 0:
                elapsed = i/(time.time() - start)
                logFile.write("{}\t{}\t{}\n".format(elapsed, i, f))
#           print_fields_by_criteria("696", rec, rec.get_fields('696'), i)
#           print_fields_by_criteria("697", rec, rec.get_fields('697'), i)
#           print_fields_by_criteria("698", rec, rec.get_fields('698'), i)
#  	    print_fields_by_criteria("951", rec, rec.get_fields('951'), i)
# 	    print_fields_by_criteria("020", rec, rec.get_fields('020'), i)
            print_fields_by_criteria("852", rec, rec.get_fields('852'), i)

logFile.write("{} records fetched in {} seconds".format(i,
                                                        (time.time() - start)))
logFile.close()
