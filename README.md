# Nationwide transactions parsing
Read CSV/midata exports from Nationwide and then do something with them.

## Setup
Place midata and statement formatted Nationwide CSVs into one or more directories.
Then call main.py like so:

```
python main.py dir1 dir2 ...
```

## Domain notes
- Inputs are CSV files, in one of two formats, with rows of transactions.
- Each transaction can be a credit or debit.
- Each file starts with a complete day of data and ends with a potentially incomplete one.
- Transactions have no unique id but the running balance can be used to (mostly) identify them.
- All transactions are in GBP.
- Each file is for one account, named in a header at the top.
- For our purposes, two transactions are the same if these are the same:
    - date
    - amount
    - balance
