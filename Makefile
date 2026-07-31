t: tests
tests: install
	python -m pytest -vv clyngor --doctest-modules -rs --failed-first
qt: quick-tests
tq: quick-tests
tf: failed-tests
failed-tests:
	python -m pytest -vv clyngor --doctest-modules -rs --failed-first --last-failed --exitfirst
quick-tests:
	python -m pytest -vv clyngor --doctest-modules --quick -rs --failed-first

run:
	python -m clyngor


# Publishing is done by .github/workflows/python-publish.yml, on a tag.
# These are for building and checking the distributions by hand.
build:
	python -m build
check: build
	python -m twine check --strict dist/*
install:
	python -m pip install -e '.[test]'


example_pyconstraint: install
	clingo examples/pyconstraint.lp -n 0
