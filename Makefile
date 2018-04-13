t: tests
tests:
	python -m pytest -vv clyngor --doctest-module -rs --failed-first

run:
	python -m clyngor



install_deps:
	python -c "import configparser; c = configparser.ConfigParser(); c.read('setup.cfg'); print(c['options']['install_requires'])" | xargs pip install -U
install:
	python setup.py install


example_pyconstraint: install
	clingo examples/pyconstraint.lp -n 0
