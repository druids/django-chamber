#
# Run install_packages as root.
# Then run local_install from current directory (for local install + app build).
#

SHELL = bash

DJANGO_DIR = dj
VIRTUAL_ENV = var/ve
LOCALPATH = $(CURDIR)
PYTHONPATH = $(LOCALPATH)/$(DJANGO_DIR)
DJANGO_TEST_PORTS = 9000-10000
SETTINGS = settings
DJANGO_SETTINGS_MODULE = $(DJANGO_DIR).settings.$(SETTINGS)
DJANGO_POSTFIX = --settings=$(DJANGO_SETTINGS_MODULE) --pythonpath=$(PYTHONPATH)
PYTHON_BIN = $(VIRTUAL_ENV)/bin
PYTHON = python2.7
PYTHON_VERSION_FULL := $(wordlist 2,4,$(subst ., ,$(shell python --version 2>&1)))
PYTHON_VERSION_MAJOR := $(word 1,${PYTHON_VERSION_FULL}).$(word 2,${PYTHON_VERSION_FULL})
TYPE = dev
OS = $(shell uname)

INIT_DATA_PATH = data
INIT_DATA_FILE = $(INIT_DATA_PATH)/init.json
INIT_DATA_MEDIA = $(INIT_DATA_PATH)/media

test_modules = test_chamber.tests

clean:
	find . -name "*.pyc" -delete;
	find . -type d -empty -delete;

cleanvirtualenv:
	rm -rf $(VIRTUAL_ENV)

cleanvar: clean cleanvirtualenv
	rm -rf $(LOCALPATH)/var

cleanall: cleanvar

pip:
	$(PYTHON_BIN)/pip install --process-dependency-links --allow-all-external -r requirements/base.txt

initvirtualenv:
	virtualenv -p $(PYTHON) --no-site-packages $(VIRTUAL_ENV)
	$(PYTHON_BIN)/pip install --upgrade pip==1.5
	$(PYTHON_BIN)/pip install setuptools --no-use-wheel --upgrade

bootstrap: initvirtualenv pip

reinstallvirtualenv: cleanvirtualenv bootstrap initvirtualenv initenv

test: clean
	$(PYTHON_BIN)/python $(LOCALPATH)/manage.py test $(test_modules)  --liveserver=localhost:$(DJANGO_TEST_PORTS) $(DJANGO_POSTFIX) -v 2

initdb:
	mkdir -p $(LOCALPATH)/var/db

syncdb:
	$(PYTHON_BIN)/python manage.py syncdb --noinput $(DJANGO_POSTFIX)

initdata: syncmedia
	if [ -a $(LOCALPATH)/$(INIT_DATA_FILE) ]; then $(PYTHON_BIN)/python manage.py loaddata $(LOCALPATH)/$(INIT_DATA_FILE) $(DJANGO_POSTFIX); fi;

resetdb:
	$(PYTHON_BIN)/python manage.py reset_db --noinput $(DJANGO_POSTFIX)
	$(MAKE) syncdb

syncmedia:
	if [ -d "$(LOCALPATH)/$(INIT_DATA_MEDIA)" ]; then\
		cp -R $(LOCALPATH)/$(INIT_DATA_MEDIA)/* $(LOCALPATH)/media/;\
	fi;

initlog:
	mkdir -p $(LOCALPATH)/var/log

initenv:
	echo -e '\nDJANGO_SETTINGS_MODULE="$(DJANGO_SETTINGS_MODULE)"' >> $(VIRTUAL_ENV)/bin/activate
	echo -e 'export DJANGO_SETTINGS_MODULE' >> $(VIRTUAL_ENV)/bin/activate

callcommand:
	@$(PYTHON_BIN)/python manage.py $(command) $(DJANGO_POSTFIX)

runserver:
	$(PYTHON_BIN)/python manage.py runserver --insecure $(DJANGO_POSTFIX)

install: cleanvar bootstrap initlog linklibrary initdb syncdb initdata initenv

update: clean cleanvirtualenv cleanjs bootstrap syncdb installjs initenv

include build/Makefile.$(OS)

linklibrary:
	ln -sf $$(pwd)/../chamber/ $$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())");
