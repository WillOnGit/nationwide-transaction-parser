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
- All transactions are for nonzero, whole quantities of pennies
- Each file is for one account, named in a header at the top.
- Statements are generally consistent, i.e. transaction dates increase monotonically and running balances are consistent with transaction amounts.
The exception is interest payments which are sometimes listed out of order and/or labelled with an "incorrect"/nominal date.
- For our purposes, two transactions are the same if these are the same:
    - date
    - amount
    - balance
- Accounts can't be mathematically guaranteed to have all transactions - there could always be extra transactions missing, even in a day, which sum to no difference.
    - therefore, we assume that if an account is consistent throughout a time period, it's probably complete.

## Tests
Run `make test` from the root directory to discover and run unit tests.
