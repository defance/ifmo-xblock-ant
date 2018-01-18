# coding=utf-8

from django.conf import settings

XBLOCK_SETTINGS = settings.XBLOCK_SETTINGS.get('IFMO_XBLOCK_ANT', {})
SELECTED_CONFIGURATION = XBLOCK_SETTINGS.get('SELECTED_CONFIGURATION', 'default')

# Список возможных конфигураций
SAMPLE_CONFIGURATIONS = {
    'npoed': {
        'ATTEMPTS_URL': 'https://de.ifmo.ru/api/public/courseAttempts?userlogin=%(user_login)s&courseid=%(course_id)s&unitid=%(unit_id)s',
        'LAB_URL': 'https://sso.openedu.ru/oauth2/authorize?response_type=code&client_id=abd6dc4ae52fee8f1226&redirect_uri=https://de.ifmo.ru/api/public/npoedOAuthEnter&state=COMMANDNAME=getCourseUnit%%26DATA=UNIT_ID=%(unit_id)s%%7CCOURSE_ID=%(course_id)s',
        'REGISTER_URL': None,
        'COURSE_INFO': 'https://de.ifmo.ru/api/public/courseInfo?courseid=%(course_id)s&unitid=%(unit_id)s',
    },
    'ifmo': {
        'ATTEMPTS_URL': 'https://de.ifmo.ru/api/public/courseAttempts?pid=%(user_login)s&courseid=%(course_id)s&unitid=%(unit_id)s',
        'LAB_URL': 'https://de.ifmo.ru/IfmoSSO?redirect=https://de.ifmo.ru/servlet/%%3FRule=EXTERNALLOGON%%26COMMANDNAME=getCourseUnit%%26DATA=UNIT_ID=%(unit_id)s|COURSE_ID=%(course_id)s',
        'REGISTER_URL': 'https://de.ifmo.ru/api/public/getCourseAccess?pid=%(user_login)s&courseid=%(course_id)s',
        'COURSE_INFO': 'https://de.ifmo.ru/api/public/courseInfo?courseid=%(course_id)s&unitid=%(unit_id)s',
    },
    'default': {
        'ATTEMPTS_URL': None,
        'LAB_URL': None,
        'REGISTER_URL': None,
        'COURSE_INFO': None,
    }
}

SAMPLE_CONFIGURATION = SAMPLE_CONFIGURATIONS.get(SELECTED_CONFIGURATION, {})
CONFIGURATION = {
    'ATTEMPTS_URL': XBLOCK_SETTINGS.get('ATTEMPTS_URL', SAMPLE_CONFIGURATION.get('ATTEMPTS_URL')),
    'LAB_URL': XBLOCK_SETTINGS.get('LAB_URL', SAMPLE_CONFIGURATION.get('LAB_URL')),
    'REGISTER_URL': XBLOCK_SETTINGS.get('REGISTER_URL', SAMPLE_CONFIGURATION.get('REGISTER_URL')),
    'COURSE_INFO': XBLOCK_SETTINGS.get('COURSE_INFO', SAMPLE_CONFIGURATION.get('COURSE_INFO')),
}


def DefaultedDescriptor(base_class, default_condition=lambda x: x is None, **args):  # pylint: disable=invalid-name
    def __get__(self, xblock, xblock_class):
        value = super(self.__class__, self).__get__(xblock, xblock_class)
        return self._default if default_condition(value) else value
    derived_dict = {
        "__get__": __get__,
    }
    derived = type("%sNoneDefaulted" % base_class.__name__, (base_class,), derived_dict)
    return derived(**args)
