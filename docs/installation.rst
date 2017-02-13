.. _installation:

Installation
============

Python/Django versions
----------------------

+----------------------+------------+
|  Python              | Django     |
+======================+============+
| 2.7, 3.4, 3.5, 3.6   | 1.7 - 1.10 |
+----------------------+------------+


Requirements
------------

 * **django** -- Chamber extends Django, therefore it is a natural dependency
 * **pyprind** -- used in CSV importers to show progress bars
 * **six** -- to provide Python 2/3 compatibility
 * **filemagic**
 * **unidecode**


Using Pip
---------
Django-chamber is not currently inside *PyPI* but in the future you will be able to use:

.. code-block:: console

    $ pip install django-chamber


Because *django-chamber* is a rapidly evolving library, the best way to install is use the source from github

.. code-block:: console

    $ pip install https://github.com/druids/django-chamber/tarball/{{ version }}#egg=django-chamber-{{ version }}

Configuration
-------------
No configuration is required as this is a utility library. Just import the stuff you need.
