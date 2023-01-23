.. _installation:

Installation
============

Python/Django versions
----------------------

+----------------------------+------------------+
|  Python                    | Django           |
+============================+==================+
| 3.5, 3.6, 3.9, 3.10, 3.11  | >=2.2 <4         |
+----------------------------+------------------+


Requirements
------------

 * **django** -- Chamber extends Django, therefore it is a natural dependency
 * **pyprind** -- used in CSV importers to show progress bars
 * **filemagic** -- to check type of the files from its content
 * **unidecode** -- to convert unicode characters to ascii


Using pip
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
