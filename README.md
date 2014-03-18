PostgreSQL index bloat reporter
===============================
Simple Python script to calcute indexes bloat size based on a csv files containing information about index sizes.

Useful if you do a periodic database restore (to eg. check database backup consistency) and have somewhere to get a fresh indexes sizes from.

CSV files can be generated from PSQL using following query:

echo "COPY (SELECT nspname || '.' || relname AS \"relation\", pg_relation_size(C.oid) AS \"size\" FROM pg_class C LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace) WHERE nspname NOT IN ('pg_catalog', 'information_schema') AND relkind = 'i' ORDER BY pg_relation_size(C.oid) DESC) TO STDOUT with CSV HEADER" | psql database_name

It has few options which may become handy:

```bash
$ ./indexbloat.py --help
Usage: indexbloat.py [options] cvsA cvsB

Options:
  -h, --help            show this help message and exit
  -i, --ignoremissing   ignore missing indexes
  -p, --pretty-mode     pretty mode
  -s, --sum             print total bloat size at the end
  -t number, --percent-threshold=number
                        pct threshold when to treat idx as bloated; default
                        102
  -b bytes, --bloat-bytes=bytes
                        minimal bloat size to display; default 0
  -c bytes, --size-threshold=bytes
                        bytes threshold when to compare idx; default 100M
```

Example output:

```bash
./indexbloat.py -ps csva.csv csvb.csv
Index idx3 size compare to clean import: 117 % (14.49G vs. 12.35G)
Index idx2 size compare to clean import: 279 % (14.49G vs. 5.18G)
Ough!  idx4 index is missing in the csvb.csv file.  Likely a problem with backup!
Total index bloat: 11.46G
```
