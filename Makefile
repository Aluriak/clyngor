t: tests
tests:
	python -m pytest -vv clyngor --doctest-module
qt: quick-tests
quick-tests:
	python -m pytest -vv clyngor --doctest-module --quick

run:
	python -m clyngor



install_deps:
	python -c "import configparser; c = configparser.ConfigParser(); c.read('setup.cfg'); print(c['options']['install_requires'])" | xargs pip install -U
install:
	python setup.py install

fullrelease:
	fullrelease
