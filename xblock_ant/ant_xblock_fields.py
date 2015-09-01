# coding=utf-8

from xblock.fields import Scope, Integer, String, Float, DateTime
# from xblock.fields import UserScope, BlockScope

from .settings import *


class AntXBlockFields(object):

    # Отображаемое имя
    display_name = String(
        display_name="Display name",
        default='AcademicNT Assignment',
        help="This name appears in the horizontal navigation at the top of "
             "the page.",
        scope=Scope.settings
    )

    # Отображаемый текстовый комментарий
    content = String(
        display_name="Content",
        default='',
        help="Text.",
        scope=Scope.settings
    )

    # Максимальный результат за задание
    points = Float(
        default=0,
        scope=Scope.user_state,
    )

    # Вес задания в рамках всего Grading'а
    weight = Float(
        display_name="Problem Weight",
        help=("Defines the number of points each problem is worth. "
              "If the value is not set, the problem is worth the sum of the "
              "option point values."),
        values={"min": 0, "step": .1},
        default = 1,
        scope=Scope.settings
    )

    # Идентификатор курса в рамках СУО ANT
    ant_course_id = String(
        display_name="Course id",
        default='',
        help="Course id in ant.",
        scope=Scope.settings
    )

    # Идентификатор юнита лабораторной работы с рамках СУО ANT
    ant_unit_id = String(
        display_name="Course id",
        default='',
        help="Unit id in ant.",
        scope=Scope.settings
    )

    # Время, отведённое на выполнение работы в ANT
    ant_time_limit = Integer(
        display_name="Time limit",
        default=0,
        help="Time limit (in minutes)",
        scope=Scope.settings
    )

    # Количество попыток, отведённое на выполнение работы в ANT
    ant_attempts_limit = Integer(
        default=0,
        help="Submission id",
        scope=Scope.settings,
    )

    # Статус выполнения задания, магическая строка: RUNNING, IDLE
    ant_status = String(
        scope=Scope.user_state,
    )

    # Время последнего обновления лимитов (время, попытки), переданных от СУО
    limit_renewal = DateTime(
        display_name="Limits renewal",
        help="When limits have been renewed.",
        default=None,
        scope=Scope.settings
    )

    # Пользовательские баллы за лабораторную
    score = Float(
        display_name="Grade score",
        default=0,
        help="Total calculated score.",
        scope=Scope.user_state
    )

    # Количество затраченных на выполнение попыток
    attempts = Integer(
        display_name="Attempts used",
        default=0,
        help="Total used attempts.",
        scope=Scope.user_state
    )

    # Идентификатор текущего задания проверки, поставленного в очередь
    # (Возможно, больше не нужен)
    celery_task_id = String(
        display_name="Task id",
        default="",
        scope=Scope.user_state
    )

    # Результат последней проверки лабораторной, полученный от СУО
    ant_result = String(
        display_name="Latest ANT result",
        default="",
        help="Latest result retrieved by grade() method",
        scope=Scope.user_state
    )

    # Адрес для вытягивания информации о выполнении
    attempts_url = String(
        display_name="Attempts API url",
        default=ATTEMPTS_URL,
        help="Url api to get latest user attempts.",
        # scope=Scope(UserScope.NONE, BlockScope.TYPE)
        scope=Scope.content,
    )

    # Адрес с лабораторной, открывается в попапе
    lab_url = String(
        display_name="Lab API url",
        default=LAB_URL,
        help="Lab url.",
        # scope=Scope(UserScope.NONE, BlockScope.TYPE)
        scope=Scope.content,
    )