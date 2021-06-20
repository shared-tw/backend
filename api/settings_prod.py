import os

import dj_database_url

from .settings import *  # noqa: F403

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = ["shared-tw.herokuapp.com", "api.shared-tw.icu"]
DATABASES["default"] = dj_database_url.config(  # noqa: F405
    conn_max_age=600, ssl_require=True
)
AUTHENTICATOR["hash_id_secret"] = os.environ["HASH_ID_SECRET"]  # noqa: F405

if "OAUTHLIB_INSECURE_TRANSPORT" in os.environ:
    del os.environ["OAUTHLIB_INSECURE_TRANSPORT"]
