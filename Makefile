.PHONY: all, test

all:
	make test

test:
	python3 -m unittest discover --pattern "*_test.py"
