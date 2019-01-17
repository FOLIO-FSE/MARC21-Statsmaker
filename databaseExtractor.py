import copy
import sys
import time
from pymarc import MARCReader
from pymarc import Field

i = 0
start = time.time()

file_out = sys.argv[2]
file_libris = sys.argv[1]
t_recs = {}

sigels = ['Za', 'Z', 'Zl', 'Enll']

def add_subjects(record, field, sigels):
    cp = copy.deepcopy(field)
    for sigel in sigels:
        f = Field(tag='698', indicators=[' ', ' '])
        f.add_subfield('5', sigel)
        for sub in cp:
            f.add_subfield(sub[0], sub[1])
        t_recs[record['001'].data.upper()].append(f)


def in_035(recs, rec):
    return ('035' in rec and
            'a' in rec['035'] and
            rec['035']['a'].upper() in recs)


def write_rec(out_file, rec):
    try:
        mrc = rec.as_marc()
        out_file.write(mrc)
        print("write")
    except Exception as ee:
        print("Något gick fel med att spara {}".format(rec['001']))
        print(ee, flush=True)

def hasSubfield(record, field, subField):
    return field in record and subField in record[field]


i = 0
dbs = 0
with open(file_libris, 'rb') as fi:
    with open(file_out, 'wb+') as fo:
        reader = MARCReader(fi, 'rb')
        for rec in reader:
            i += 1
            if i % 10000 == 0:
                elapsed = i/(time.time() - start)
                print("{}\t{}\t{}".format(elapsed, i, file_libris), flush=True)
            if '698' in rec:
                for fs in rec.get_fields('698'):
                    if '5' in fs and 'b' in fs and fs['5'] == 'Z' and fs['b'] == 'ZDBAS':
                        dbs +=1
                        write_rec(fo, rec)
                        print("Databas {}".format(dbs))
