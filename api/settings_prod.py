import dj_database_url

from .settings import *

DEBUG = False
ALLOWED_HOSTS = ["shared-tw.herokuapp.com"]
DATABASES["default"] = dj_database_url.config(conn_max_age=600, ssl_require=True)
