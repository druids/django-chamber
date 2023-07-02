from django.urls import re_path

from test_chamber import views  # pylint: disable=E0401


urlpatterns = [
    re_path(r'^current_time_backend/$', views.current_datetime, name='current-datetime')
]
