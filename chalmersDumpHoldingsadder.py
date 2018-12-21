import copy
import sys
import time
from pymarc import MARCReader
from pymarc import Field

i = 0
start = time.time()

file_in = sys.argv[1]
file_out = sys.argv[2]
file_libris = sys.argv[3]
t_recs = {}

sigels = ['Za', 'Z', 'Zl', 'Enll']


def code_to_sigel(code):
    if code.startswith('abib'):
        return 'Za'
    elif code.startswith('hbib'):
        return 'Z'
    elif code.startswith('lbib'):
        return 'Zl'
    elif code.startswith('mat'):
        return 'Enll'
    else:
        raise ValueError('wrong library code supplied{}'.format(code))


def add_holding(record, sigel):
    f = Field(tag='852', indicators=[' ', ' '])
    f.add_subfield('5', sigel)
    f.add_subfield('b', sigel)
    return f


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
    except Exception as ee:
        print("Något gick fel med att spara {}".format(rec['001']))
        print(ee, flush=True)


i = 0
p = 0
sh = 0
s = 0
adds = 0
without_zsh = 0
si_bib_ids = {}
with open(file_in, 'rb') as fi:
    reader = MARCReader(fi, 'rb')
    for rec in reader:
        iD = rec['001'].data.upper()
        t_recs[iD] = []
        i += 1
        sigels = set()
        if i % 10000 == 0:
            elapsed = i/(time.time() - start)
            print("{}\t{}\t{}".format(elapsed, i, file_in), flush=True)
        if '907' in rec and 'c' in rec['907']:
            if rec['907']['c'] == 'p':
                p += 1
                for fi in rec.get_fields('852'):
                    sigels.add(fi['5'])
                    adds += 1
            elif rec['907']['c'] == 's':
                s += 1
                for fe in rec.get_fields('945'):
                    c = code_to_sigel(fe['l'])
                    sigels.add(c)
                    adds += 1
            else:
                print('else1', flush=True)
            si_bib_ids[iD] = rec['907']['a']
        else:
            print("else", flush=True)
            print("{}\t{}".format(iD, list(sigels)), flush=True)
        for sigel in sigels:
            t_recs[iD].append(add_holding(rec, sigel))
        if '698' in rec:
            sh += 1
            for fs in rec.get_fields('698'):
                add_subjects(rec, fs, sigels)
        else:
            without_zsh += 1
    elapsed = i/(time.time() - start)
    print("85{}\t{}\t{}".format(elapsed, i, len(t_recs)), flush=True)
missing = set()
saves = 0
match_001 = 0
match_035 = 0
found_ids = set()
with open(file_out, 'wb+') as fo:
    with open(file_libris, 'rb') as fl:
        reader = MARCReader(fl, 'rb')
        j = 0
        smart = time.time()
        for l_rec in reader:
            has_cth_698 = ('698' in l_rec and
                           '5' in l_rec['698'] and
                           l_rec['698']['5'] in sigels)
            if has_cth_698:
                print("698", flush=True)
            iD = l_rec['001'].data.upper()
            j += 1
            if j % 10000 == 0:
                elapsed = j/(time.time() - smart)
                print("{}\t{}\t{}".format(elapsed, j, file_in), flush=True)
            l_rec.remove_fields('852')
            l_rec.remove_fields('866')
            if iD in t_recs:
                match_001 += 1
                for t_field in t_recs[iD]:
                    l_rec.add_field(t_field)
                write_rec(fo, l_rec)
                saves += 1
                found_ids.add(iD)
            elif in_035(t_recs, l_rec):
                match_035 += 1
                old_id = l_rec['035']['a'].upper()
                for t_field in t_recs[old_id]:
                    l_rec.add_field(t_field)
                write_rec(fo, l_rec)
                saves += 1
                found_ids.add(old_id)
            else:
                missing.add(iD)
print("All written. The following ids where not fount", flush=True)

set_sierra = set(t_recs.keys())
unmatched = set_sierra - found_ids
for nolletta in unmatched:
    print(si_bib_ids[nolletta])
print("001:or i sierra utan match i 001/035a i Libris", flush=True)
print(len(unmatched))
# print(list(unmatched), flush=True)

print("Missing from Sierra:\t\t{}".format(len(missing)))
# print(list(missing))
print("S in 907$c:\t\t{}".format(s))
print("P in 907$c:\t\t{}".format(p))
print("Added subject headings:\t\t{}".format(sh))
print("Saves:\t\t{}".format(saves))
print("Added 852s:\t\t{}".format(adds))
print("Records from Sierra:\t\t{}".format(i))
print("Records from Libris:\t\t{}".format(j))
print("Sierras 001 i Libris 001:\t\t{}".format(match_001))
print("Sierras 001 i Libris 035:\t\t{}".format(match_035))
print("Utan lokala ämnesord i 698:\t\t{}".format(without_zsh))
