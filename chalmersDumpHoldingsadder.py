from os import listdir
from os.path import isfile, join
import copy
import sys
import time
import json
from pymarc import MARCReader
from pymarc import Field


def main():
    ''' this is where it all starts... '''
    # Initialize counters and lists and variables
    sigels = ['Za', 'Z', 'Zl', 'Enll']
    num_sierra_records = 0
    start = time.time()
    sierra_dump_path = sys.argv[1]
    file_out_path = sys.argv[2]
    libris_dump_path = sys.argv[3]
    path_035 = sys.argv[4]
    temp_records = {}  # Holdings info derived from Sierra records
    num_sierra_records = 0
    num_with_local_subjects = 0
    added_sigels = 0
    num_without_local_subjects = 0
    sierra_bib_ids = {}
    num_dupe_001s = 0
    dupe_001s = set()
    num_enigma = 0

    # Open and read Sierra dump files
    only_files = [f for f in listdir(sierra_dump_path)
                  if isfile(join(sierra_dump_path, f))]
    for file_path in only_files:
        with open(join(sierra_dump_path, file_path), 'rb') as sierra_dump:
            reader = MARCReader(sierra_dump, 'rb')
            for sierra_record in reader:

                # current record Id. Upper so isbns will be matched.
                iD = sierra_record['001'].data.upper()

                try:
                    # Add sierra bib id (.bxxxxxx) to dictionary for later use
                    sierra_bib_ids[iD] = sierra_record['907']['a']

                    if iD == 'FOLIOSTORAGE':
                        # If enigma record. just count it and then leave
                        # the for loop
                        num_enigma += 1
                        continue
                    elif iD in temp_records:
                        # If more than one record with the same 001 exists,
                        # data will be appended to the same temporary record.
                        print("001 Already in temp_records!! {}".format(iD))
                        num_dupe_001s += 1
                        dupe_001s.add(iD)  # Add Id for late print out.
                    else:
                        # Create new temporary record.
                        # Data that we want to move from Sierra to Libris
                        # will be added to this temporary record.
                        temp_records[iD] = []

                    # Add new holdings info to temporary record in the form of
                    # sigels only.
                    sigels_in_sierra = get_sigels_to_add(sierra_record)
                    for sigel in sigels_in_sierra:
                        added_sigels += len(sigels_in_sierra)
                        temp_records[iD].append(create_new_holding(sigel))

                    # Add databases even if they do not have sigel
                    if is_chalmers_db(sierra_record):
                        print("Added database to Sierra records")
                        temp_records[iD].append(create_new_holding('Z'))

                    # Add local subject headings to temporary record
                    if '698' in sierra_record:
                        num_with_local_subjects += 1
                        temp_records[iD].extend(get_subjects(sierra_record,
                                                             sigels_in_sierra))
                    else:
                        num_without_local_subjects += 1

                    # Display progress
                    num_sierra_records += 1
                    if num_sierra_records % 10000 == 0:
                        print("{} recs/s\t{}".format(
                            round(num_sierra_records/(time.time() - start)),
                            num_sierra_records), flush=True)
                except ValueError as value_error:
                    print("Värdefel: {} för {}".format(value_error, iD))

    # Display progress and print statistics at end of Sierra file iteration
    print("Done reading Sierra records in {}s."
          .format(round((time.time() - start))))
    print("\tTotal records:{}".format(num_sierra_records))
    print("\tNumber of enigma records: {}".format(num_enigma))
    print("\tRecords with data to add to Libris:{}".format(len(temp_records)))
    print("# recs without local Subject headings:\t{}"
          .format(num_without_local_subjects))
    print("# recs with local Subject headings:\t{}"
          .format(num_with_local_subjects))
    print("Added 852s:\t{}".format(added_sigels))
    print("Duplicate 001:s # ids (unique):\t{}({})"
          .format(num_dupe_001s, len(dupe_001s)))
    # Initialize counters and lists for Libris file iteration
    missing = []
    saved_records = 0
    match_001 = 0
    match_035 = 0
    found_ids = set()
    num_libris_records = 0
    libris_start = time.time()
    has_local_subject_heading = 0
    num_has_also_035_match = 0
    has_also_035_match = set()
    found_035s = []
    removed_fields = {}
    # Open result file for writing
    with open(file_out_path, 'wb+') as file_out:
        # Open and read Libris dump file
        with open(libris_dump_path, 'rb') as libris_dump:
            reader = MARCReader(libris_dump, 'rb')
            for libris_record in reader:
                is_db = is_chalmers_db(libris_record)
                iD = libris_record['001'].data.upper()
                old_id = (libris_record['035']['9'].upper()
                          if ('035' in libris_record
                              and '9' in libris_record['035']) else '')
                current_holdings = get_current_holdings(libris_record)

                # remove unwanted holding fields for all records but DB:s
                if is_db:
                    print("Keeping DB Libris 852 for {}".format(iD))
                else:
                    tags_to_delete_not_db = ['500', '506', '520', '852', '856']
                    for t in tags_to_delete_not_db:
                        delete_by_tag(libris_record, t)

                # Remove unwanted Holdings fields for all records
                tags_to_delete = ['040', '041', '082', '084', '541', '562',
                                  '563', '599', '600', '610', '611', '630',
                                  '651', '863', '866', '876', '949']
                for t in tags_to_delete:
                    delete_by_tag(libris_record, t)

                # Add fields from temporary records to Libris record
                # For 001 - 001 matches
                if iD in temp_records:  # We have a 001 match
                    # print out any diff in Holdings info on Sigel level
                    print_hold_diff(libris_record, temp_records[iD])
                    
                    for temp_field in temp_records[iD]:
                        if temp_field['5'] in current_holdings:
                            libris_record.add_field(temp_field)

                    # Write record to disc
                    write_rec(file_out, libris_record)
                    # Check if Libris record's 035$a mathes any Sierra 001:s
                    if old_id in temp_records:
                            num_has_also_035_match += 1
                            has_also_035_match.add(old_id)
                    saved_records += 1
                    found_ids.add(iD)
                    match_001 += 1

                # Add fields from temporary records to Libris record
                # For 001 - 035a matches
                elif old_id in temp_records:
                    # print out any diff in Holdings info on Sigel level
                    print_hold_diff(libris_record, temp_records[old_id])

                    for temp_field in temp_records[old_id]:
                        if temp_field['5'] in current_holdings:
                            libris_record.add_field(temp_field)

                    # write record to another file for 001 replacement in
                    # Sierra
                    with open(path_035, 'ab+') as file_035:
                        write_rec(file_035, libris_record)

                    # Write to results file
                    write_rec(file_out, libris_record)
                    saved_records += 1
                    found_ids.add(old_id)
                    found_035s.append(old_id)
                    match_035 += 1

                # No match. Get the Libris instance and holdings Ids for
                # Print out.
                else:
                    for id_placeholder in libris_record.get_fields('887'):
                        if '5' in id_placeholder:
                            a = id_placeholder['a']
                            jstring = a.replace('{lrub}', '{')
                            jstring = jstring.replace('{lcub}', '}')
                            xl_id = json.loads(jstring)['@id']
                            missing.append([iD, xl_id])

                # Display progress
                num_libris_records += 1
                print_progress(num_libris_records, libris_start)

            # Display progress at end of iteration
            print_progress(num_libris_records, libris_start)

    # We are done. Calculate and print out some statistics
    print("All written. The following sierra ids where not found in Libris")
    set_sierra = set(temp_records.keys())
    unmatched = set_sierra - found_ids
    for unmatched_id in unmatched:
        print(sierra_bib_ids[unmatched_id])
    print("removed fields from LIBRIS recs:\n{}".format(removed_fields))
    print("001:s in Sierra with no match in 001/035a in Libris: {}"
          .format(len(unmatched)))
    print(list(unmatched))
    print('============================')
    print("Libris records missing from Sierra:\t\t{}".format(len(missing)))
    for miss in list(missing):
        print("{}\t{}".format(miss[0], miss[1]))
    print('============================')
    print("Number of Saved records to be sent to Libris:\t\t{}"
          .format(saved_records))
    print("Records from Sierra:\t\t{}".format(num_sierra_records))
    print("Records from Libris:\t\t{}".format(num_libris_records))
    print("Sierras 001 in Libris 001:\t\t{}".format(match_001))
    print("Sierras 001 in Libris 035:\t\t{}".format(match_035))
    print("Libris records with local subject headings:\t\t{}".format(
        has_local_subject_heading))
    print("Both 001 and 035$a matches in Sierra (unique ids):\t{}({})".format(
        num_has_also_035_match, len(has_also_035_match)))
    print(has_also_035_match)
    print('============================')


def delete_by_tag(record, tag):
    fs = record.get_fields(tag)
    for f in [f for f in fs if '5' in f]:
        record.remove_field(f)
    # if (num_f_start-num_f_end) > 0:
        # print("Successfully removed {} fields {} from {}"
        #       .format(num_f_start-num_f_end, tag, record['001']))


def print_hold_diff(libris_record, sierra_record):
    '''compares the sigels held and prints out any differences between
    Sierra and Libris'''
    libris_holdings = get_current_holdings(libris_record)
    sierra_holdings = set()
    for field in sierra_record:
        if '5' in field:
            sierra_holdings.add(field['5'])

    # Libris has something that Sierra has not.
    more_in_xl = libris_holdings-sierra_holdings
    if more_in_xl:
        for id_placeholder in libris_record.get_fields('887'):
            if '5' in id_placeholder and id_placeholder['5'] in more_in_xl:
                # Get that broken libris holdings id out of there!
                a = id_placeholder['a']
                jstring = a.replace('{lrub}', '{')
                jstring = jstring.replace('{lcub}', '}')
                xl_id = json.loads(jstring)['@id']
                print(("More holdings in Libris: {} than in Sierra {} "
                       "for {}\t{}\t{}")
                      .format(libris_holdings, sierra_holdings,
                              libris_record['001'],
                              xl_id, id_placeholder['5']))

    # Sierra has something Libris has not
    if sierra_holdings-libris_holdings:
        print("More holdings in Sierra: {} than in Libris {} for {}"
              .format(sierra_holdings, libris_holdings, libris_record['001']))


def get_current_holdings(libris_record):
    current_holdings = set()
    for field in libris_record.get_fields('887'):
        if '5' in field:
            current_holdings.add(field['5'])
    return current_holdings


def print_progress(num_records, start):
    '''print progress of script'''
    if num_records % 10000 == 0:
        elapsed = round(num_records/(time.time() - start))
        print("{} recs/sec\t{}".format(
            elapsed, num_records), flush=True)


def code_to_sigel(code):
    '''convert a code to a sigel'''
    if code.startswith('abib'):
        return 'Za'
    elif code.startswith('hbib'):
        return 'Z'
    elif code.startswith('lbib'):
        return 'Zl'
    elif code.startswith('mat'):
        return 'Enll'
    else:
        raise ValueError('wrong library code supplied {}'.format(code))


def is_chalmers_db(record):
    '''Determines if record is a Database record'''
    if '698' in record:
        for fs in record.get_fields('698'):
            is_db = ('5' in fs
                     and 'b' in fs
                     and fs['5'] == 'Z'
                     and fs['b'] == 'ZDBAS')
            if is_db:
                print("DB! {} {}".format(fs, record['001']))
                return True
    return False


def create_new_holding(sigel):
    '''Create basic 852 field with only sigel.'''
    new_holding = Field(tag='852', indicators=[' ', ' '])
    new_holding.add_subfield('5', sigel)
    new_holding.add_subfield('b', sigel)
    return new_holding


def get_subjects(sierra_record, sigels):
    '''Collect local subject headings from records and return a set of
    new fields of those for all sigels owning the record'''
    subjects_to_return = set()
    for field in sierra_record.get_fields('698'):
        field_copy = copy.deepcopy(field)
        for sigel in sigels:
            new_field = Field(tag='698', indicators=[' ', ' '])
            new_field.add_subfield('5', sigel)
            for subfield in field_copy:
                if subfield[0] != '5':
                    new_field.add_subfield(subfield[0], subfield[1])
                subjects_to_return.add(new_field)
    return subjects_to_return


def in_035(recs, rec):
    '''Given a "list" of record ids, checks if 035$9 of a record exists in
    that list'''
    if '035' not in rec:
        return False
    for subfield in rec['035'].get_subfields('9', 'a'):
        if subfield and subfield.upper() in recs:
            return True
    return False


def write_rec(out_file, rec):
    '''Write a marc record to file'''
    try:
        mrc = rec.as_marc()
        out_file.write(mrc)
    except Exception as ee:
        print("ERROR when saving record with 001: {}".format(rec['001']))
        print(ee)
        print(rec)


def get_sigels_to_add(sierra_record):
    '''Get all (but no dupes) sigels from 945$l and 852$ai'''
    sigels = set()
    for field in sierra_record.get_fields('852'):
        sigels.add(field['5'])
    for field in sierra_record.get_fields('945'):
        c = code_to_sigel(field['l'])
        sigels.add(c)
    return set(filter(None.__ne__, sigels))


if __name__ == '__main__':
    main()
