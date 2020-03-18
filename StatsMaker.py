import sys
import time
import glob
from pymarc import MARCReader


def add_stats(stats, a):
    if a not in stats:
        stats[a] = 1
    else:
        stats[a] += 1


def type_of_record(record):
    l06 = record.leader[6]
    l07 = record.leader[7]
    f008 = (record['008'] and record['008'].data)
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


def concatenate_subfields(field):
    return (repr([x.encode('utf-8') for x in field.subfields]) if
            field and field.subfields else '-')


def print_field_and_record_data(name, record, field, record_index):
    print(name + '\t' + record.leader + '\t' +
          (record['001'].data if '001' in record else '-') + '\t' +
          (record['006'].data if '006' in record else '-') + '\t' +
          (record['007'].data if '007' in record else '-') + '\t' +
          (record['008'].data if '008' in record else '-') + '\t' +
          (field['a'] if field and 'a' in field else '-') + '\t' +
          (field['4'] if field and '4' in field else '-') + '\t' +
          (field.indicators[0]
           if field and field.indicators and len(field.indicators) > 0
           else '-') + '\t' +
          (field.indicators[1] if field and field.indicators and len(field.indicators) > 1 else '-') + '\t' +
          (field.tag if field else '-') + '\t' +
          concatenate_subfields(field) + '\t' +
          (type_of_record(record)) + '\t' +
          (record.title() or '-') + '\t' +
          ("Record_{}".format(record_index) or '-') + '\t' +
          (field and field['z'] or '-') + '\t' +
          (record['907']['a'] if '907' in record and 'a' in record['907']
           else '-') + '\t' +
          (record['907']['b'] if '907' in record and 'b' in record['907']
           else '-') + '\t')


def print_fields_by_criteria(name, record, fields_to_print, record_index):
    if fields_to_print:
        for field in fields_to_print:
            print_field_and_record_data(name, record, field, record_index)
    else:
        print_field_and_record_data(name, record, None, record_index)


i = 0
start = time.time()
f990a = {}
f998d = {}
f998e = {}

files = glob.glob(sys.argv[1])[::-1]
print(files)

for f in files:
    with open(f, 'rb') as fh:
        reader = MARCReader(fh, 'rb')
        for rec in reader:
            i += 1

            if i % 1000 == 0:
                elapsed = i/(time.time() - start)
                print("{}\t{}\t{}\n".format(elapsed, i, f))

print("{} records fetched in {} seconds".format(i,
                                                (time.time() - start)))
