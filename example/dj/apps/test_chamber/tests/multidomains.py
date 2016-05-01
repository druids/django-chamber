from __future__ import unicode_literals

from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from germanium.tools import assert_equal, assert_raises

from chamber.multidomains.domain import get_domain_choices, get_user_class, get_current_domain, get_domain, Domain
from chamber.multidomains.urlresolvers import reverse

from test_chamber.models import BackendUser, FrontendUser


class MultidomainsTestCase(TestCase):

    def test_get_domain_choices(self):
        choices = get_domain_choices()
        assert_equal(len(choices), 2)
        assert_equal(choices[0][1], 'backend')
        assert_equal(choices[1][1], 'frontend')
        assert_equal(choices[0][0], 1)
        assert_equal(choices[1][0], 2)

    def test_get_current_user_class(self):
        assert_equal(get_user_class(), BackendUser)

    def test_get_user_class(self):
        assert_equal(get_domain(settings.BACKEND_SITE_ID).user_class, BackendUser)
        assert_equal(get_domain(settings.FRONTEND_SITE_ID).user_class, FrontendUser)

    def test_get_current_domain(self):
        assert_equal(get_current_domain().name, 'backend')

    def test_get_domain(self):
        assert_equal(get_domain(settings.BACKEND_SITE_ID).name, 'backend')
        assert_equal(get_domain(settings.FRONTEND_SITE_ID).name, 'frontend')
        assert_raises(ImproperlyConfigured, get_domain, 3)

    def test_get_domain_url(self):
        assert_equal(get_domain(settings.BACKEND_SITE_ID).url, 'http://localhost:8000')
        assert_equal(get_domain(settings.FRONTEND_SITE_ID).url, 'https://localhost')

    def test_new_domain_port(self):
        assert_equal(Domain('testA', 'http', 'localhost', 'dj.backend_urls', 'test_chamber.BackendUser').port, 80)
        assert_equal(Domain('testB', 'https', 'localhost', 'dj.backend_urls', 'test_chamber.BackendUser').port, 443)
        assert_equal(Domain('testC', 'http', 'localhost', 'dj.backend_urls', 'test_chamber.BackendUser', 443).port, 443)
        assert_equal(Domain('testD', 'https', 'localhost', 'dj.backend_urls', 'test_chamber.BackendUser', 80).port, 80)
        assert_raises(ImproperlyConfigured, Domain, 'testF', 'hbbs', 'localhost', 'dj.backend_urls',
                      'test_chamber.BackendUser')

        assert_equal(Domain('testA', 'http', 'localhost', 'dj.backend_urls', 'test_chamber.BackendUser').url,
                     'http://localhost')
        assert_equal(Domain('testB', 'https', 'localhost', 'dj.backend_urls', 'test_chamber.BackendUser').url,
                     'https://localhost')
        assert_equal(Domain('testC', 'http', 'localhost', 'dj.backend_urls', 'test_chamber.BackendUser', 443).url,
                     'http://localhost:443')
        assert_equal(Domain('testD', 'https', 'localhost', 'dj.backend_urls', 'test_chamber.BackendUser', 80).url,
                     'https://localhost:80')

    def test_reverse(self):
        assert_equal(reverse('current-datetime'), '/current_time_backend/')
        assert_equal(reverse('current-datetime', site_id=settings.BACKEND_SITE_ID), '/current_time_backend/')
        assert_equal(reverse('current-datetime', site_id=settings.FRONTEND_SITE_ID), '/current_time_frontend/')

        assert_equal(reverse('current-datetime', site_id=settings.BACKEND_SITE_ID, add_domain=True),
                     'http://localhost:8000/current_time_backend/')
        assert_equal(reverse('current-datetime', site_id=settings.FRONTEND_SITE_ID, add_domain=True),
                     'https://localhost/current_time_frontend/')

        assert_equal(reverse('current-datetime', site_id=settings.BACKEND_SITE_ID, add_domain=True,
                             urlconf='frontend_urls'),
                     'http://localhost:8000/current_time_frontend/')
        assert_equal(reverse('current-datetime', site_id=settings.FRONTEND_SITE_ID, add_domain=True,
                             urlconf='backend_urls'),
                     'https://localhost/current_time_backend/')

        assert_equal(reverse('current-datetime', qs_kwargs={'a': 1}), '/current_time_backend/?a=1')

        assert_raises(ImproperlyConfigured, reverse, 'current-datetime', site_id=3)
