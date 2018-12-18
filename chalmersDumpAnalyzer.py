import sys
import time
import glob
from pymarc import MARCReader

i = 0
start = time.time()

files = glob.glob(sys.argv[1])[::-1]

for f in files:
    with open(f, 'rb') as fh:
        reader = MARCReader(fh, 'rb')
        f001s = set()
        misses_sigel = []
        misses_852 = []
        for rec in reader:
            i += 1
            if i % 10000 == 0:
                elapsed = i/(time.time() - start)
                print("{}\t{}\t{}".format(elapsed, i, f))
            if not rec['001'].data in f001s:
                f001s.add(rec['001'].data)
            else:
                print("Duplicate found! \t{}".format(rec['001'].data))
            if '852' not in rec:
                misses_852.append(rec['001'].data)
                print("Missing 852 for \t{}".format(rec['001']))
            else:
                for fe in rec.get_fields('852'):
                    if fe['5'] not in ['Za', 'Zl', 'Z', 'Enll']:
                        misses_sigel.append(rec['001'].data)
                        print("Missing sigel for \t{}".format(rec['001']))
                        print(fe['5'])
        print("Missing sigels: \t{}".format(len(misses_sigel)))
        print("Missing 852: \t{}".format(len(misses_852)))
        print("Total records:\t{}".format(len(f001s)))
