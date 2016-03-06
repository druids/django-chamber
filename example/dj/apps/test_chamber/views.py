import datetime

from django.http import HttpResponse


def current_datetime(request):
    return HttpResponse('<html><body>It is now %s.</body></html>' % datetime.datetime.now())
