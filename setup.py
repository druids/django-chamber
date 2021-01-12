from setuptools import setup, find_packages

from chamber.version import get_version


setup(
    name='django-chamber',
    version=get_version(),
    description='Utilities library meant as a complement to django-is-core.',
    author='Lubos Matl, Oskar Hollmann',
    author_email='matllubos@gmail.com, oskar@hollmann.me',
    url='http://github.com/druids/django-chamber',
    packages=find_packages(include=['chamber']),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Framework :: Django',
    ],
    install_requires=[
        'Django>=2.2',
        'Unidecode>=1.1.1',
        'pyprind>=2.11.2',
        'filemagic>=1.6',
    ],
    extras_require={
        'boto3storage': ['django-storages<2.0', 'boto3'],
    },
)
