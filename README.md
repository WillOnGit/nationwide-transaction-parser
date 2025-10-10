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

## Domain notes
- Inputs are CSV files, in one of two formats, with rows of transactions.
- Each transaction can be a credit or debit.
- Each file starts with a complete day of data and ends with a potentially incomplete one.
- Transactions have no unique id but the running balance can be used to (mostly) identify them.
- All transactions are in GBP.
- Each file is for one account, named in a header at the top.
