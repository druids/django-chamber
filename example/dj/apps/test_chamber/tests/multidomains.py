from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from chamber.multidomains.domain import Domain, get_current_domain, get_domain, get_domain_choices, get_user_class
from chamber.multidomains.urlresolvers import reverse

from germanium.tools import assert_equal, assert_raises  # pylint: disable=E0401

from test_chamber.models import BackendUser, FrontendUser  # pylint: disable=E0401


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
        assert_equal(Domain('testA', 'dj.backend_urls', 'test_chamber.BackendUser',
                            protocol='http', hostname='localhost').port, 80)
        assert_equal(Domain('testB', 'dj.backend_urls', 'test_chamber.BackendUser',
                            protocol='https', hostname='localhost').port, 443)
        assert_equal(Domain('testC', 'dj.backend_urls', 'test_chamber.BackendUser',
                            protocol='http', hostname='localhost', port=443).port, 443)
        assert_equal(Domain('testD', 'dj.backend_urls', 'test_chamber.BackendUser',
                            protocol='https', hostname='localhost', port=80).port, 80)
        assert_raises(ImproperlyConfigured, Domain, 'testF', 'dj.backend_urls', 'test_chamber.BackendUser',
                      protocol='hbbs', hostname='localhost')
        assert_equal(Domain('testD', 'dj.backend_urls', 'test_chamber.BackendUser',
                            url='https://localhost:80').port, 80)
        assert_equal(Domain('testD', 'dj.backend_urls', 'test_chamber.BackendUser',
                            url='https://localhost').port, 443)

        assert_equal(Domain('testA', 'dj.backend_urls', 'test_chamber.BackendUser',
                            protocol='http', hostname='localhost').url, 'http://localhost')
        assert_equal(Domain('testB', 'dj.backend_urls', 'test_chamber.BackendUser',
                            protocol='https', hostname='localhost').url, 'https://localhost')
        assert_equal(Domain('testC', 'dj.backend_urls', 'test_chamber.BackendUser',
                            protocol='http', hostname='localhost', port=443).url, 'http://localhost:443')
        assert_equal(Domain('testD', 'dj.backend_urls', 'test_chamber.BackendUser',
                            protocol='https', hostname='localhost', port=80).url, 'https://localhost:80')

    def test_reverse(self):
        assert_equal(reverse('current-datetime'), '/current_time_backend/')
        assert_equal(reverse('current-datetime', site_id=settings.BACKEND_SITE_ID), '/current_time_backend/')
        assert_equal(reverse('current-datetime', site_id=settings.FRONTEND_SITE_ID), '/current_time_frontend/')

        assert_equal(reverse('current-datetime', site_id=settings.BACKEND_SITE_ID, add_domain=True),
                     'http://localhost:8000/current_time_backend/')
        assert_equal(reverse('current-datetime', site_id=settings.FRONTEND_SITE_ID, add_domain=True),
                     'https://localhost/current_time_frontend/')

        assert_equal(reverse('current-datetime', site_id=settings.BACKEND_SITE_ID, add_domain=True,
                             urlconf='dj.frontend_urls'),
                     'http://localhost:8000/current_time_frontend/')
        assert_equal(reverse('current-datetime', site_id=settings.FRONTEND_SITE_ID, add_domain=True,
                             urlconf='dj.backend_urls'),
                     'https://localhost/current_time_backend/')

        assert_equal(reverse('current-datetime', qs_kwargs={'a': 1}), '/current_time_backend/?a=1')

        assert_raises(ImproperlyConfigured, reverse, 'current-datetime', site_id=3)
