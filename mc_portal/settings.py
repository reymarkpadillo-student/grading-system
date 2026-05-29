

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent



SECRET_KEY = 'django-insecure-b5i8k$5-jnf-t@_xg$-w4ow)z!ifxqm+we-!7v(^4fxa21reb('

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'portal',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mc_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mc_portal.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

IS_ADMIN = lambda request: request.user.is_superuser
IS_FACULTY = lambda request: request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_teacher)
IS_ANY_STAFF = lambda request: request.user.is_staff

UNFOLD = {
    "SITE_TITLE": "CSS Department Admin",
    "SITE_HEADER": "CSS Department Portal",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": lambda request: "/static/img/Picture2.png",
        "dark":  lambda request: "/static/img/Picture2.png",
    },
    "COLORS": {
        "primary": {
            "50":  "250 253 255",
            "100": "240 249 255",
            "200": "224 242 254",
            "300": "186 230 253",
            "400": "125 211 252",
            "500": "56 189 248",
            "600": "2 132 199",
            "700": "3 105 161",
            "800": "7 89 133",
            "900": "15 23 42",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Academics",
                "separator": True,
                "items": [
                    {
                        "title": "Year Levels",
                        "icon": "stairs",
                        "link": "/admin/portal/yearlevel/",
                        "permission": IS_ADMIN,
                    },
                    {
                        "title": "Blocks / Sections",
                        "icon": "groups",
                        "link": "/admin/portal/section/",
                        "permission": IS_ADMIN,
                    },
                    {
                        "title": "Subjects",
                        "icon": "menu_book",
                        "link": "/admin/portal/subject/",
                        "permission": IS_ADMIN,
                    },
                    {
                        "title": "Schedules",
                        "icon": "calendar_month",
                        "link": "/admin/portal/schedule/",
                        "permission": IS_FACULTY,
                    },
                ],
            },
            {
                "title": "Grading",
                "separator": True,
                "items": [
                    {
                        "title": "Records & Grades",
                        "icon": "grade",
                        "link": "/admin/portal/record/",
                        "permission": IS_ANY_STAFF,
                    },
                    {
                        "title": "Grade Periods",
                        "icon": "assignment",
                        "link": "/admin/portal/gradeperiod/",
                        "permission": IS_ANY_STAFF,
                    },
                    {
                        "title": "Assessments",
                        "icon": "quiz",
                        "link": "/admin/portal/assessment/",
                        "permission": IS_FACULTY,
                    },
                    {
                        "title": "Assessment Scores",
                        "icon": "scoreboard",
                        "link": "/admin/portal/assessmentscore/",
                        "permission": IS_FACULTY,
                    },
                    {
                        "title": "Attendance",
                        "icon": "fact_check",
                        "link": "/admin/portal/attendance/",
                        "permission": IS_ANY_STAFF,
                    },
                    {
                        "title": "Grading Templates",
                        "icon": "description",
                        "link": "/admin/portal/gradingtemplate/",
                        "permission": IS_FACULTY,
                    },
                ],
            },
            {
                "title": "Users",
                "separator": True,
                "items": [
                    {
                        "title": "All Users",
                        "icon": "person",
                        "link": "/admin/auth/user/",
                        "permission": IS_ADMIN,
                    },
                    {
                        "title": "User Profiles",
                        "icon": "manage_accounts",
                        "link": "/admin/portal/userprofile/",
                        "permission": IS_ADMIN,
                    },
                ],
            },
            {
                "title": "Settings",
                "separator": True,
                "items": [
                    {
                        "title": "School Years",
                        "icon": "event_note",
                        "link": "/admin/portal/schoolyear/",
                        "permission": IS_ADMIN,
                    },
                    {
                        "title": "Semesters",
                        "icon": "date_range",
                        "link": "/admin/portal/semester/",
                        "permission": IS_ADMIN,
                    },
                    {
                        "title": "Active Terms",
                        "icon": "toggle_on",
                        "link": "/admin/portal/schoolyearsemester/",
                        "permission": IS_ADMIN,
                    },
                    {
                        "title": "Periods",
                        "icon": "timeline",
                        "link": "/admin/portal/period/",
                        "permission": IS_ADMIN,
                    },
                    {
                        "title": "Grade Parts (Weights)",
                        "icon": "balance",
                        "link": "/admin/portal/gradepart/",
                        "permission": IS_ADMIN,
                    },
                    {
                        "title": "Assessment Weights",
                        "icon": "percent",
                        "link": "/admin/portal/assessmenttypeweight/",
                        "permission": IS_ADMIN,
                    },
                ],
            },
        ],
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
