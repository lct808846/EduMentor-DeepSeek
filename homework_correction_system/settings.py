"""
Django settings for homework_correction_system project.

Generated by 'django-admin startproject' using Django 3.2.25.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-9#-wnbzq1545sdam-+1dfsy=#pojd7@sfzojq@6g0_wxkth5(^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'correction_system',
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

ROOT_URLCONF = 'homework_correction_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'homework_correction_system.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (Uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DeepSeek API 配置
DEEPSEEK_API_KEY = 'sk-f83ac616b83247f99ca96ab6c5694132'

# 认证相关设置
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# 表单部件样式设置
# 注意：这里不能直接设置 attrs 属性，因为表单部件是类而不是实例
# 我们将在应用的 forms.py 中自定义表单部件样式

# 移除以下不正确的设置
# from django import forms
# FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

# # 设置表单小部件的默认样式类
# WIDGET_CLASSES = {
#     'default': 'form-control',
#     'checkbox': 'form-check-input',
#     'radio': 'form-check-input',
#     'select': 'form-select',
# }

# # 应用表单样式
# forms.TextInput.attrs['class'] = WIDGET_CLASSES['default']
# forms.EmailInput.attrs['class'] = WIDGET_CLASSES['default']
# forms.URLInput.attrs['class'] = WIDGET_CLASSES['default']
# forms.NumberInput.attrs['class'] = WIDGET_CLASSES['default']
# forms.PasswordInput.attrs['class'] = WIDGET_CLASSES['default']
# forms.Textarea.attrs['class'] = WIDGET_CLASSES['default']
# forms.DateInput.attrs['class'] = WIDGET_CLASSES['default']
# forms.DateTimeInput.attrs['class'] = WIDGET_CLASSES['default']
# forms.TimeInput.attrs['class'] = WIDGET_CLASSES['default']
# forms.CheckboxInput.attrs['class'] = WIDGET_CLASSES['checkbox']
# forms.RadioSelect.attrs['class'] = WIDGET_CLASSES['radio']
# forms.Select.attrs['class'] = WIDGET_CLASSES['select']
# forms.SelectMultiple.attrs['class'] = WIDGET_CLASSES['select']


