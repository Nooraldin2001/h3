import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Env
env = environ.Env(
	DEBUG=(bool, False),
	SECRET_KEY=(str, "change-me-in-production"),
	ALLOWED_HOSTS=(list, []),
	LANGUAGE_CODE=(str, "ar"),
	TIME_ZONE=(str, "Asia/Dubai"),
	USE_PYMYSQL=(bool, False),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))  # optional

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Database
DATABASE_URL = env.str(
	"DATABASE_URL",
	default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
)
DATABASES = {"default": env.db_url_config(DATABASE_URL)}

# Apps
INSTALLED_APPS = [
	"django.contrib.admin",
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	"django.contrib.sitemaps",
	"django_htmx",
	"parler",
	"import_export",
	"ckeditor",
	"plates",
]

MIDDLEWARE = [
	"django.middleware.security.SecurityMiddleware",
	"whitenoise.middleware.WhiteNoiseMiddleware",
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.locale.LocaleMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
	"django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "h3auctions.urls"

TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"DIRS": [BASE_DIR / "templates"],
		"APP_DIRS": True,
		"OPTIONS": {
			"context_processors": [
				"django.template.context_processors.debug",
				"django.template.context_processors.request",
				"django.contrib.auth.context_processors.auth",
				"django.contrib.messages.context_processors.messages",
				"django.template.context_processors.i18n",
				"plates.context_processors.site_settings",
			],
		},
	},
]

WSGI_APPLICATION = "h3auctions.wsgi.application"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
	{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
	{"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
	{"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
	{"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = env("LANGUAGE_CODE")
TIME_ZONE = env("TIME_ZONE")
USE_I18N = True
USE_TZ = True

LANGUAGES = [
	("ar", "Arabic"),
	("en", "English"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# Static & Media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# WhiteNoise
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Parler
PARLER_LANGUAGES = {
	"default": {
		"fallbacks": ["en"],
		"hide_untranslated": False,
	},
	1: (
		{"code": "ar"},
		{"code": "en"},
	),
}

# CKEditor basic config
CKEDITOR_CONFIGS = {
	"default": {
		"toolbar": "Basic",
	}
}


