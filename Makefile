t: tests
tests:
	python -m pytest -vv clyngor --doctest-module

run:
	python -m clyngor


upload:
	python setup.py sdist upload

install:
	- yes y | pip uninstall clyngor
	python setup.py install

remote_install:
	- yes y | pip uninstall clyngor
	pip install clyngor
