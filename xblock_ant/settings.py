# coding=utf-8

"""
Настройки модуля. Вообще, всё это стоит хранить в отдельном файле, например,
yml или ещё каком-нибудь. Но реальность слишком жестока, чтобы такое можно
было провернуть...
"""

# Текущая выбранная конфигурация
SELECTED_CONFIGURATION = 'npoed'

# Список возможных конфигураций
CONFIGURATIONS = {
    'npoed': {
        'ATTEMPTS_URL': 'http://de.ifmo.ru/api/public/courseAttempts?userlogin=%(user_login)s&courseid=%(course_id)s&unitid=%(unit_id)s',
        'LAB_URL': 'http://sso.openedu.ru/oauth2/authorize?response_type=code&client_id=abd6dc4ae52fee8f1226&redirect_uri=https://de.ifmo.ru/api/public/npoedOAuthEnter&state=COMMANDNAME=getCourseUnit%%26DATA=UNIT_ID=%(unit_id)s%%7CCOURSE_ID=%(course_id)s',
        'REGISTER_URL': None,
        'COURSE_INFO': 'http://de.ifmo.ru/api/public/courseInfo?courseid=%(course_id)s&unitid=%(unit_id)s',
    },
    'ifmo': {
        'ATTEMPTS_URL': 'http://de.ifmo.ru/api/public/courseAttempts?pid=%(user_login)s&courseid=%(course_id)s&unitid=%(unit_id)s',
        'LAB_URL': 'http://de.ifmo.ru/IfmoSSO?redirect=http://de.ifmo.ru/servlet/%%3FRule=EXTERNALLOGON%%26COMMANDNAME=getCourseUnit%%26DATA=UNIT_ID=%(unit_id)s|COURSE_ID=%(course_id)s',
        'REGISTER_URL': 'http://de.ifmo.ru/api/public/getCourseAccess?pid=%(user_login)s&courseid=%(course_id)s',
        'COURSE_INFO': 'http://de.ifmo.ru/api/public/courseInfo?courseid=%(course_id)s&unitid=%(unit_id)s',
    },
    'default': {
        'ATTEMPTS_URL': None,
        'LAB_URL': None,
        'REGISTER_URL': None,
        'COURSE_INFO': None,
    }
}

CONFIGURATION = CONFIGURATIONS.get(SELECTED_CONFIGURATION)
