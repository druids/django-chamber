from dj.settings.base import *  # pylint: disable=E0401


DEBUG = TEMPLATE_DEBUG = THUMBNAIL_DEBUG = True

SITE_ID = BACKEND_SITE_ID

ALLOWED_HOSTS = [DOMAINS.get(SITE_ID).hostname]

# URL with protocol (and port)
PROJECT_URL = DOMAINS.get(SITE_ID).url

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_DIR, 'var', 'db', 'sqlite.db'),
        'USER': '',
        'PASSWORD': '',
    },
}

ROOT_URLCONF = DOMAINS.get(SITE_ID).urlconf

STATIC_ROOT = ''

# Additional locations of static files
STATICFILES_DIRS = (
    STATICFILES_ROOT,
)
