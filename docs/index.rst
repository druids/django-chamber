.. django-chamber documentation master file, created by
   sphinx-quickstart on Wed Aug 26 20:27:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

##############
Django-chamber
##############


.. image:: https://travis-ci.org/druids/django-chamber.svg?branch=master
   :target: https://travis-ci.org/druids/django-chamber

.. image:: https://api.codacy.com/project/badge/Grade/012d28c820fd4b19a783618c05d7a0a9
   :target: https://www.codacy.com/app/lukas-rychtecky/django-chamber?utm_source=github.com&utm_medium=referral&utm_content=druids/django-chamber&utm_campaign=badger

.. image:: https://coveralls.io/repos/github/druids/django-chamber/badge.svg?branch=master
   :target: https://coveralls.io/github/druids/django-chamber?branch=master

.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
   :target: https://opensource.org/licenses/BSD-3-Clause

Chamber contains a collection of useful base model classes, form fields, model fields, decorators, or other shortcuts to aid web development in Django.

One can think of it as a toolbox with utilities that were too small to justify creating a standalone library and therefore ended up here. Hence the name *Chamber*. Its purpose is not unlike the discontinued `EasyMode <https://pypi.python.org/pypi/django-easymode>`_ library.

********
Overview
********

Features
========
The most noteworthy part of Chamber is the alternative base class for Django models called :code:`SmartModel`. It provides following additional features:

* adds :code:`created_at` and :code:`changed_at` datetime fields on derived models,
* splits the save method of Django model into several methods :code:`_pre_save`, :code:`_save`, :code:`_post_save` for readability,
* keeps track of whether the instance being saved is a new one or whether it is an update to an existing one,
* keeps track of which fields changed during the save method and this info is available even in the :code:`_post_save` method,
* provides way to unclutter the save methods by declaring several types of **model dispatchers**, useful e.g. for sending notifications based on changes on the instance.

Other useful components include:

* AuditModel -- adds :code:`created_at` and :code:`changed_at` fields to the basic Django model,
* SmartQuerySet -- adds :code:`fast_distinct` method to querysets (useful for PostgreSQL),
* several enum classes such as :code:`ChoicesNumEnum` or :code:`SequenceChoiceEnum`,
* new Django-style shortcuts such as :code:`get_object_or_none`, :code:`change_and_save`, or :code:`bulk_change_and_save`.
* :code:`MigrationLoadFixture` class that supports loading Django fixtures inside a database migration
* ...and more.

Contributing & Documentation
============================
You are welcomed to contribute at https://github.com/druids/django-chamber. There is an example project in the repository. Your feature should be added to this example project with tests as well as the documentation.

# Go to the `example` directory and call `make install` to install it.
# Run tests using `make test`.

Documentation is available at https://django-chamber.readthedocs.org/en/latest.

Known Issues
============
* this documentation is a work in progress, needs a lot of attention
* SmartModel extends the AuditModel and therefore always adds `created_at` and `changed_at` fields to the model which is not always desirable

*******
Content
*******

.. toctree::
   :maxdepth: 5

   installation
   forms
   models
   dispatchers
   transactions
   utils
   shortcuts
