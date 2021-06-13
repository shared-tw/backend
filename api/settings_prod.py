import os

import dj_database_url

from .settings import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["shared-tw.herokuapp.com"]
DATABASES["default"] = dj_database_url.config(  # noqa: F405
    conn_max_age=600, ssl_require=True
)
if "OAUTHLIB_INSECURE_TRANSPORT" in os.environ:
    del os.environ["OAUTHLIB_INSECURE_TRANSPORT"]
