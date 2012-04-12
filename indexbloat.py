#!/usr/bin/python

import sys, time, csv, re
from optparse import OptionParser

"""
Simple Python script to calcute indexes bloat size based on a csv files
containing information about index sizes.

Useful if you do a periodic database restore (to eg. check database
backup consistency) and have somewhere to get a fresh indexes sizes
from.

CSV files can be generated from PSQL using following query:

echo "COPY (SELECT nspname || '.' || relname AS \"relation\",
pg_relation_size(C.oid) AS \"size\" FROM pg_class C LEFT JOIN
pg_namespace N ON (N.oid = C.relnamespace) WHERE nspname NOT IN
('pg_catalog', 'information_schema') AND relkind = 'i' ORDER BY
pg_relation_size(C.oid) DESC) TO STDOUT with CSV HEADER" | psql
database_name
"""

def readCSV(filename):
    csvHook = csv.reader(open(filename, 'rb'), delimiter=',')

    # initialise dictionary
    result = {}

    for k, v in csvHook:
        # parse key through regexp to strip out the first part
        k = re.search('\w+.(.*)', k)

        # not interested in pg internal indexes
        if not re.match('^pg_', k.group(1)) and k.group(1) is not '':
            result[k.group(1)] = v

    return result

def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fG' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fM' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fK' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size

def main():
    # process options and arguments
    usage = "usage: %prog [options] cvsA cvsB"
    parser = OptionParser(usage)

    parser.add_option("-i", "--ignoremissing", dest="ignmissidxs",
            help="ignore missing indexes",
            action="store_false", default=True)
    parser.add_option("-p", "--pretty-mode", dest="pretty",
            help="pretty mode",
            action="store_true", default=False)
    parser.add_option("-s", "--sum", dest="sum",
            help="print total bloat size at the end",
            action="store_true")
    parser.add_option("-t", "--percent-threshold", dest="pctthrs",
            help="pct threshold when to treat idx as bloated; default 102",
            action="store", default=102, metavar="number")
    parser.add_option("-b", "--bloat-bytes", dest="bloatbytes",
            help="minimal bloat size to display; default 0",
            action="store", default=0, metavar="bytes")
    parser.add_option("-c", "--size-threshold", dest="bytesthrs",
            help="bytes threshold when to compare idx; default 100M",
            action="store", default=100000000, metavar="bytes")

    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("incorrect number of arguments; you must specify both "
                     "cvsA and cvsB file locations")

    # load data from CVS files
    cvsA = readCSV(args[0]) # production data
    cvsB = readCSV(args[1]) # clean import data

    sum = 0 # we are going to use it to track total bloat size

    for name, size in cvsA.iteritems():
        if name in cvsB:
            # difference in %
            diff = long(size) * 100 / long(cvsB[name])
            # difference in bytes
            diff_bytes = long(size) - long(cvsB[name])

            if (diff > options.pctthrs and long(size) > options.bytesthrs and
                    long(diff_bytes) > long(options.bloatbytes)):
                if options.pretty:
                    print ("Index %s size compare to clean import: %s %% (%s "
                           "vs. %s)" % (name, diff, convert_bytes(size),
                                       convert_bytes(cvsB[name])))
                else:
                    print ("index %s, %s %%, %s/%s" % (name, diff,
                            convert_bytes(size), convert_bytes(cvsB[name])))

                # total it up to the total idx bloat size
                sum = sum + diff_bytes
        else:
            if options.ignmissidxs:
                if options.pretty:
                    print ("Ough!  %s index is missing in the %s file. "
                           "Likely a problem with backup!" % (name, args[1]))
                else:
                    print "index %s missing in %s file!" % (name, args[1])

    # print total bloat size
    if options.sum:
        if options.pretty:
            print "Total index bloat: %s" % convert_bytes(sum)
        else:
            print "total bloat: %s" % sum

if __name__ == '__main__':
    main()

