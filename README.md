# django-chamber

[![Build
Status](https://travis-ci.org/druids/django-chamber.svg?branch=master)](https://travis-ci.org/druids/django-chamber)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/012d28c820fd4b19a783618c05d7a0a9)](https://www.codacy.com/app/lukas-rychtecky/django-chamber?utm_source=github.com&utm_medium=referral&utm_content=druids/django-chamber&utm_campaign=badger)
[![Coverage
Status](https://coveralls.io/repos/github/druids/django-chamber/badge.svg?branch=master)](https://coveralls.io/github/druids/django-chamber?branch=master)
[![Licence](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

Chamber contains a collection of useful base model classes, form fields, model fields, decorators, or other shortcuts to aid web development in Django.

One can think of it as a toolbox with utilities that were too small to justify creating a standalone library and therefore ended up here. Hence the name **Chamber**.

## Features

The most noteworthy part of Chamber is the alternative base class for Django models called `SmartModel`. It provides following additional features:

Other useful components include:

* AuditModel -- adds `created_at` and `changed_at` fields to the basic Django model,
* SmartQuerySet -- adds `fast_distinct` method to querysets (useful for PostgreSQL),
* several enum classes such as `ChoicesNumEnum` or `SequenceChoiceEnum`,
* new Django-style shortcuts such as `get_object_or_none`, `change_and_save`, or `bulk_change_and_save`.
* `MigrationLoadFixture` class that supports loading Django fixtures inside a database migration
* ...and more.

## Contributing & Documentation

You are welcomed to contribute at https://github.com/druids/django-chamber. There is an example project in the repository. Your feature should be added to this example project with tests as well as the documentation.

1. Go to the `example` directory and call `make install` to install it.
2. Run tests using `make test`.

## Known Issues

* documentation of this library is a work in progress, needs a lot of attention
* SmartModel extends the AuditModel and therefore always adds `created_at` and `changed_at` fields to the model which is not always desirable

## License

This library is licenced under the 3-clause BSD licence. See the LICENCE file for details.
