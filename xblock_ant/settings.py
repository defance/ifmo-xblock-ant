# coding=utf-8

"""
Настройки модуля. Вообще, всё это стоит хранить в отдельном файле, например,
yml или ещё каком-нибудь. Но реальность слишком жестока, чтобы такое можно
было провернуть...
"""

# Информация о попытках по почтовому адресу пользователя, курсу и модулю (юниту)
# ATTEMPTS_URL = 'http://de.ifmo.ru/api/public/courseAttempts?pid=%(user_id)s&courseid=%(course_id)s&unitid=%(unit_id)s'
ATTEMPTS_URL = 'http://de.ifmo.ru/api/public/courseAttempts?userlogin=%(user_email)s&courseid=%(course_id)s&unitid=%(unit_id)s'

# Адрес лабораторной работы по курсу и модулю (юниту)
# LAB_URL = "http://de.ifmo.ru/IfmoSSO?redirect=http://de.ifmo.ru/servlet/%%3FRule=EXTERNALLOGON%%26COMMANDNAME=getCourseUnit%%26DATA=UNIT_ID=%(unit_id)s|COURSE_ID=%(course_id)s"
LAB_URL = "http://community.npoed.ru/oauth/authorize.php?response_type=code&client_id=1930ca015234cfc686e2f085a30787dca47294113e1a8e3bbfb5686689e35d29&redirect_uri=https://de.ifmo.ru/api/public/npoedOAuthEnter&state=COMMANDNAME=getCourseUnit%%26DATA=UNIT_ID=%(unit_id)s%%7CCOURSE_ID=%(course_id)s"

# Адрес регистрации пользователя на курс внутри СУО
REGISTER_URL = 'http://de.ifmo.ru/api/public/getCourseAccess?pid=%(sso_id)s&courseid=%(course_id)s'