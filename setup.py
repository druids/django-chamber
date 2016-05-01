from setuptools import setup, find_packages

from chamber.version import get_version


setup(
    name="django-chamber",
    version=get_version(),
    description="Utilities library meant as a complement to django-is-core.",
    author="Lubos Matl,Oskar Hollmann",
    author_email="matllubos@gmail.com,oskarhollmann@gmail.com",
    url="http://github.com/druids/django-chamber",
    packages=find_packages(),
    package_dir={"chamber": "chamber"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Framework :: Django",
    ],
    install_requires = [
        'Django >= 1.6',
        'Unidecode>=0.04.17',
    ],
)
