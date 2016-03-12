PYTHON2 = python2.7
VIRTUAL_ENV = var/ve
PYTHON_BIN = $(VIRTUAL_ENV)/bin

initvirtualenv:
	virtualenv -p $(PYTHON2) --no-site-packages $(VIRTUAL_ENV)
	$(PYTHON_BIN)/pip install --upgrade pip==7.1.2
	$(PYTHON_BIN)/pip install setuptools --no-use-wheel --upgrade

clean: cleanvar
	find . -name "*.pyc" -delete;
	find . -type d -empty -delete;

cleanvar:
	rm -rf $(VIRTUAL_ENV)

pip:
	$(PYTHON_BIN)/pip install --process-dependency-links --allow-all-external -r requirements.txt

install: clean initvirtualenv pip

tests:
	$(VIRTUAL_ENV)/bin/nose2
