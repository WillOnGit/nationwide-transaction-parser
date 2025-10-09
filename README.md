# Nationwide transactions parsing
Read CSV/midata exports from Nationwide and then do something with them.

## Setup
Make a directory with a midata format file and a statement format.
Then create env.py like so:

```
# constants
TRANSACTIONS_DIRECTORY="/path/to/a/directory"
TEST_MIDATA="midata_filename.csv"
TEST_STATEMENT="statement_filename.csv"
```

Finally, run `python main.py`.
