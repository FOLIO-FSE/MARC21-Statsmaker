import sys
import time
from pymarc import MARCReader

i = 0
start = time.time()
with open(sys.argv[1], 'rb') as fh:
    reader = MARCReader(fh, 'rb')
    for rec in reader:
        i += 1
        if i % 1000 == 0:
            elapsed = i/(time.time() - start)
            print("{}\t{}".format(elapsed, i))
        current_holdings = []
        for field in rec.get_fields('852'):
            if '5' in field:
                if field['5'] in current_holdings:
                    print("{} already in record {}"
                          .format(field['5'], rec['001']), flush=True)
                current_holdings.append(field['5'])
print("{} records fetched in {} seconds"
      .format(i, (time.time() - start)))
