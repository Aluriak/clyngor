t: tests
tests:
	python -m pytest -vv clyngor --doctest-module


upload:
	python setup.py sdist upload

install:
	yes y | pip uninstall clyngor
	pip install clyngor
