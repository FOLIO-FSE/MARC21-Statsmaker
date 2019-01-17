import copy
import sys
import time
from pymarc import MARCReader
from pymarc import Field


# METHODS
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


# Determines if record is a Database record
def is_chalmers_db(record):
    if '698' in record:
        for fs in record.get_fields('698'):
            return ('5' in fs
                    and 'b' in fs
                    and fs['5'] == 'Z'
                    and fs['b'] == 'ZDBAS')
    else:
        return False


# Create basic 852 field with only sigel.
def create_new_holding(sigel):
    new_holding = Field(tag='852', indicators=[' ', ' '])
    new_holding.add_subfield('5', sigel)
    new_holding.add_subfield('b', sigel)
    return new_holding


# Collect local subject headings from records and return a list of
# new fields of those for all sigels owning the record
def get_subjects_to_add(sierra_record, sigels):
    for field in sierra_record.get_fields('698'):
        field_copy = copy.deepcopy(field)
        for sigel in sigels:
            new_field = Field(tag='698', indicators=[' ', ' '])
            new_field.add_subfield('5', sigel)
            for subfield in field_copy:
                new_field.add_subfield(subfield[0], subfield[1])
            yield new_field


# Given a "list" of record ids, checks if 035$a of a record exists in that list
def in_035(recs, rec):
    return ('035' in rec and
            'a' in rec['035'] and
            rec['035']['a'].upper() in recs)


# Write a marc record to file
def write_rec(out_file, rec):
    try:
        mrc = rec.as_marc()
        out_file.write(mrc)
    except Exception as ee:
        print("ERROR when saving record with 001: {}".format(rec['001']))
        print(ee, flush=True)
        print(rec)


# Get all (but no dupes) sigels from 945$l and 852$a
def get_sigels_to_add(sierra_record):
    sigels = set()
    for field in sierra_record.get_fields('852'):
        sigels.add(field['5'])
    for field in sierra_record.get_fields('945'):
        c = code_to_sigel(field['l'])
        sigels.add(c)
    return set(filter(None.__ne__, sigels))

# END METHODS


# Initialize counters and lists and variables
sigels = ['Za', 'Z', 'Zl', 'Enll']
num_sierra_records = 0
start = time.time()
sierra_dump_path = sys.argv[1]
file_out_path = sys.argv[2]
libris_dump_path = sys.argv[3]
temp_records = {}
num_sierra_records = 0
num_with_local_subjects = 0
added_sigels = 0
num_without_local_subjects = 0
sierra_bib_ids = {}
num_dupe_001s = 0
dupe_001s = set()

# Open and read Sierra dump file
with open(sierra_dump_path, 'rb') as sierra_dump:
    reader = MARCReader(sierra_dump, 'rb')
    for sierra_record in reader
        # TODO: check the ~220 records not having any data to bring over

        # current record Id. Upper so isbns will be matched.
        iD = sierra_record['001'].data.upper()

        # Add bib id (.bxxxxxx) to dictionary for later use
        sierra_bib_ids[iD] = sierra_record['907']['a']

        # Create new temporary record.
        # Data that we want to move from Sierra to Libris will be added
        # to this temporary record.
        # If more than one record with the same 001 exists,
        # data will be appended to the same temporary record.
        if iD in temp_records:
            # print("001 Already in temp_records!! {}".format(iD))
            num_dupe_001s += 1
            dupe_001s.add(iD)
        else:
            temp_records[iD] = []

        # Add new holdings info to temporary record
        sigels = get_sigels_to_add(sierra_record)
        for sigel in sigels:
            added_sigels += len(sigels)
            temp_records[iD].append(create_new_holding(sigel))

        # Add local subject headings to temporary record
        # TODO: Make sure we do not add same subject headings twice
        # in case of 001 duplicates
        if '698' in sierra_record:
            num_with_local_subjects += 1
            for subject in get_subjects_to_add(sierra_record, sigels):
                temp_records[iD].append(subject)
        else:
            num_without_local_subjects += 1

        # Display progress
        num_sierra_records += 1
        if num_sierra_records % 10000 == 0:
            print("{} recs/s\t{}".format(
                round(num_sierra_records/(time.time() - start)),
                num_sierra_records), flush=True)

    # Display progress and print statistics at end of Sierra file iteration
    print("Done reading Sierra records in {}s.".format(
        round((time.time() - start))))
    print("\tTotal records:{}".format(num_sierra_records))
    print("\tRecords with data to add to Libris:{}".format(len(temp_records)))
    print("# recs without local Subject headings:\t{}".format(
        num_without_local_subjects))
    print("# recs with local Subject headings:\t{}".format(
        num_with_local_subjects))
    print("Added 852s:\t{}".format(added_sigels))
    print("Duplicate 001:s # ids (unique):\t{}({})".format(
        num_dupe_001s, len(dupe_001s)))


# Initialize counters and lists for Libris file iteration
missing = set()
saved_records = 0
match_001 = 0
match_035 = 0
found_ids = set()
num_libris_records = 0
libris_start = time.time()
has_local_subject_heading = 0
num_has_also_035_match = 0
has_also_035_match = set()


# Open result file for writing
with open(file_out_path, 'wb+') as file_out:

    # Open and read Libris dump file
    with open(libris_dump_path, 'rb') as libris_dump:
        reader = MARCReader(libris_dump, 'rb')
        for libris_record in reader:

            iD = libris_record['001'].data.upper()

            has_cth_698 = ('698' in libris_record and
                           '5' in libris_record['698'] and
                           libris_record['698']['5'] in sigels)
            if has_cth_698:
                has_local_subject_heading += 1
                if not is_chalmers_db(libris_record):
                    print("Not db! {}".format(iD))

            # Remove Holdings data since we will add new.
            libris_record.remove_fields('852')
            libris_record.remove_fields('866')

            # Add fields from temporary records to Libris record
            if iD in temp_records:  # We have a 001 match
                match_001 += 1
                for temp_field in temp_records[iD]:
                    libris_record.add_field(temp_field)
                write_rec(file_out, libris_record)
                saved_records += 1
                found_ids.add(iD)
                # Check if Libris record's 035$a mathes any Sierra 001:s
                if in_035(temp_records, libris_record):
                    old_id = libris_record['035']['a'].upper()
                    num_has_also_035_match += 1
                    has_also_035_match.add(old_id)
            elif in_035(temp_records, libris_record):  # We have a 035$a match
                match_035 += 1
                old_id = libris_record['035']['a'].upper()
                for temp_field in temp_records[old_id]:
                    libris_record.add_field(temp_field)
                write_rec(file_out, libris_record)
                saved_records += 1
                found_ids.add(old_id)
            else:
                missing.add(iD)

            # Display progress
            num_libris_records += 1
            if num_libris_records % 10000 == 0:
                elapsed = num_libris_records/(time.time() - libris_start)
                print("{} recs/s\t{}".format(
                    round(elapsed), num_libris_records), flush=True)

        # Display progress at end of iteration
        if num_libris_records % 10000 == 0:
            elapsed = round(num_libris_records/(time.time() - libris_start))
            print("{} recs/sec\t{}".format(
                elapsed, num_libris_records), flush=True)

# We are done. Calculate and print out some statistics if wanted
print("All written. The following ids where not found", flush=True)
set_sierra = set(temp_records.keys())
unmatched = set_sierra - found_ids
# for unmatched_id in unmatched:
#    print(sierra_bib_ids[unmatched_id])

print("001:s in Sierra with no match in 001/035a in Libris: {}".format(
    len(unmatched)), flush=True)
# print(list(unmatched), flush=True)

print("Missing from Sierra:\t\t{}".format(len(missing)))
# print(list(missing))

print("Saves:\t\t{}".format(saved_records))

print("Records from Sierra:\t\t{}".format(num_sierra_records))
print("Records from Libris:\t\t{}".format(num_libris_records))
print("Sierras 001 i Libris 001:\t\t{}".format(match_001))
print("Sierras 001 i Libris 035:\t\t{}".format(match_035))
print("Libris records with local subject headings:\t\t{}".format(
    has_local_subject_heading))
print("Both 001 and 035$a matches in Sierra (unique ids):\t{}({})".format(
    num_has_also_035_match, len(has_also_035_match)))
# print(has_also_035_match)
