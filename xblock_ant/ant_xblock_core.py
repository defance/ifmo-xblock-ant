# -*- coding: utf-8 -*-

from ifmo_celery_grader.models import GraderTask
from ant_xblock.ant_xblock_fields import AntXBlockFields
from ant_xblock import utils as ant_utils
from celery.states import PENDING
from courseware.models import StudentModule
from xblock.core import XBlock
from xblock.fragment import Fragment
from webob.exc import HTTPFound, HTTPForbidden
from django.db import transaction
from xmodule.util.duedate import get_extended_due_date

import datetime
import json
import pytz
import requests

from ant_xblock.tasks import submit_delayed_ant_precheck, submit_ant_check, reserve_task
from .settings import *


class AntXBlock(AntXBlockFields, XBlock):

    icon_class = 'problem'
    has_score = True
    # always_recalculate_grades = True

    def student_view(self, context):
        """
        Отображение блока в LMS.

        :param context:
        :return:
        """

        template_context = self._get_student_context()

        fragment = Fragment()
        fragment.add_content(self._render_template('static/templates/student_view.html', template_context))
        fragment.add_javascript(self._get_resource('static/js/student_view.js'))
        fragment.initialize_js('AntXBlockShow')
        return fragment

    def studio_view(self, context):
        """
        Отображение блока в студии.

        :param context:
        :return:
        """

        template_context = {
            'metadata': json.dumps({
                'display_name': self.display_name,
                'course_id': self.ant_course_id,
                'unit_id': self.ant_unit_id,
                'content': self.content,
                'time_limit': self.ant_time_limit,
                'attempts_limit': self.ant_attempts_limit,
                'attempts_url': self.attempts_url,
                'lab_url': self.lab_url,
            }),
        }

        fragment = Fragment()
        fragment.add_content(self._render_template('static/templates/studio_view.html', template_context))
        fragment.add_javascript(self._get_resource('static/js/studio_view.js'))
        fragment.initialize_js('AntXBlockEdit')
        return fragment

    def get_score(self):
        """
        Текущий балл за лабораторную.

        :return:
        """
        return {
            'score': 0,
        }

    def max_score(self):
        """
        Максимально возможный балл за лабораторную.

        :return:
        """
        return self.points

    @XBlock.handler
    def start_lab(self, request, suffix=''):
        """
        Начало выполнение лабораторной.

        Вызывается, когда пользователь нажал кнопку "Начать лабораторную".

        :param request:
        :param suffix:

        :return:
        """

        # Начинаем лабораторную только в том случае, если срок не истёк
        if self._past_due():
            return HTTPForbidden(comment="Past due")

        # Собираем мета-данные для блока
        lab_meta = {
            'sso_id': self.runtime.get_real_user(self.runtime.anonymous_student_id).username,
            'course_id': self.ant_course_id,
            'unit_id': self.ant_unit_id,
        }

        # Нужно ли нам создавать новое отложенное задание для проверки?
        need_new_task = False

        # Если нет связанного с блоком задания...
        if self.celery_task_id is None:

            # ... то нужно
            need_new_task = True

        else:

            # В противном случае создадим новое задание только, если в очереди
            # на выполнение не висит другого, которое привязано к этому блоку
            try:
                task = GraderTask.objects.get(task_id=self.celery_task_id)
                if task.task_state != PENDING:
                    need_new_task = True

            # Если задания нет вообще, то, естественно, создаём
            except GraderTask.DoesNotExist:
                need_new_task = True

        # А теперь просто перечеркнём всё, что мы делали раньше. Дело в том,
        # что задания могут быть разных типов, и задание "проверить результат
        # через некоторое время" не должен блокировать задание "проверить
        # результат прямое сейчас". Чтобы таких блокировок не происходило, мы
        # просто будет создавать новое задание на отложенную проверку каждый
        # раз, когда пользователь начинает выполнение лабораторной. Хотя на
        # самом деле, нажатие кнопки "начать лабораторную" совсем не означает,
        # что пользователь начал новую лабораторную, а только лишь то, что он
        # открыл окно, таким образом, открыватется простор для start-флуда,
        # который нужно прикрыть.
        # И вообще, нужно решить, что делать с мёртвым кодом выше.
        need_new_task = True

        # Если нужно задание, резервируем его и ставим в очередь
        if need_new_task:
            task = reserve_task(self,
                                grader_payload=self._get_grader_payload(),
                                system_payload=self._get_system_payload(),
                                student_input=self._get_student_input(),
                                save=True,
                                task_type='ANT_START')

            # Запоминаем, что с этим блоком связано задание
            self.celery_task_id = submit_delayed_ant_precheck(task).task_id

        self.save_now()

        # Особенность ANT: пользователя нужно зарегистрировать на курс, прежде
        # чем показывать ему лабораторную
        register_url = REGISTER_URL % lab_meta
        requests.post(register_url)

        # Делаем редирект на страницу с лабораторной
        lab_url = self.lab_url % lab_meta
        return HTTPFound(location=lab_url)

    @XBlock.json_handler
    def check_lab(self, data, suffix=''):
        """
        Проверить лабораторную работу.

        Вызывается, когда пользователь нажал кнопку "Проверить лабораторную".

        :param data:
        :param suffix:
        :return:
        """

        # Проверяем лабораторную только в том случае, если срок не истёк
        if self._past_due():
            return json.dumps({
                "result": "error",
                "message": "Время, отведённое на лабораторную работу, истекло.",
            })

        task = reserve_task(self,
                            grader_payload=self._get_grader_payload(),
                            system_payload=self._get_system_payload(),
                            student_input=self._get_student_input(),
                            save=True,
                            task_type='ANT_CHECK')
        submit_ant_check(task, countdown=0)
        return json.dumps({
            "result": "success",
            "message": "Лабораторная работа поставлена в очередь на проверку.",
        })

    @XBlock.json_handler
    def save_settings(self, data, suffix=''):
        """
        Сохранить настройки XBlock'а.

        :param data:
        :param suffix:
        :return:
        """
        self.display_name = data.get('display_name')
        self.ant_course_id = data.get('course_id', '')
        self.ant_unit_id = data.get('unit_id', '')
        self.content = data.get('content', '')
        self.ant_time_limit = data.get('time_limit', 0)
        self.ant_attempts_limit = data.get('attempts_limit', 0)
        self.attempts_url = data.get('attempts_url', ATTEMPTS_URL)
        self.lab_url = data.get('lab_url', LAB_URL)
        return '{}'

    @XBlock.json_handler
    def get_user_data(self, data, suffix=''):
        """
        Получить состояние определённого пользователя.

        :param data:
        :param suffix:
        :return:
        """
        user_id = data.get('user_id')
        module = StudentModule.objects.get(module_state_key=self.location,
                                           student__username=user_id)
        return {
            'state': module.state,
        }

    @transaction.autocommit
    def save_now(self):
        """
        Сохранить модуль в обход транзакций.

        :return:
        """
        self.save()

    def _get_student_context(self):
        """
        Получить контекст текущего пользователя для отображения шаблона.
        :return:
        """
        return {
            'student_state': json.dumps(
                {
                    'score': {
                        'earned': self.score,
                        'max': self.weight,
                    },
                    'attempts': {
                        'used': self.attempts,
                        'limit': self.ant_attempts_limit,
                    },
                    'time': {
                        'limit': self.ant_time_limit,
                    },
                    'ant': {
                        'course': self.ant_course_id,
                        'unit': self.ant_unit_id,
                    },
                    'meta': {
                        'name': self.display_name,
                        'text': self.content,
                    },
                    'ant_status': self.ant_status,
                }
            ),
            'is_staff': getattr(self.xmodule_runtime, 'user_is_staff', False),
            'past_due': self._past_due(),

            # This is probably studio, find out some more ways to determine this
            'is_studio': self.scope_ids.user_id is None
        }

    @staticmethod
    def _get_resource(file_name):
        """
        Получить содержимое файла из ресурсов.

        :param file_name: Имя файла

        :return: Содержимое
        """
        return ant_utils.resource_string(file_name, package_name='ant_xblock')

    @staticmethod
    def _render_template(template_name, context=None):
        """
        Отрендерить шаблон.

        :param template_name: Имя шаблона
        :param context: Контекст для отображения

        :return: Содержимое
        """
        return ant_utils.render_template(template_name, context=context, package_name='ant_xblock')

    def _get_task_data(self):
        """
        Данные, связанные с заданием для отображения в студии.

        :return:
        """
        return {
            'user_id': self.runtime.get_real_user(self.runtime.anonymous_student_id).id,
            'course_id': unicode(self.course_id),
            'module_id': unicode(self.location),
            'ant_course_id': self.ant_course_id,
            'ant_unit_id': self.ant_unit_id,
            'ant_time_limit': self.ant_time_limit,
            'max_score': self.weight,
            'lab_url': self.lab_url,
            'attempts_url': self.attempts_url,
        }

    def _get_grader_payload(self):
        """
        Данные, завясящие исключительно от модуля, но не возволяющие
        идентифицировать сам модуль.

        :return:
        """
        return {
            'ant_course_id': self.ant_course_id,
            'ant_unit_id': self.ant_unit_id,
            'ant_time_limit': self.ant_time_limit,
            'attempts_url': self.attempts_url,
        }

    def _get_system_payload(self):
        """
        Данные, позволяющие идентифицировать сам модуль.

        :return:
        """
        return {
            'user_id': self.scope_ids.user_id,
            'course_id': unicode(self.course_id),
            'module_id': unicode(self.location),
            'max_score': self.weight,
        }

    def _get_student_input(self):
        """
        Пользовательский ввод.

        :return:
        """
        return {
            'user_id': self.runtime.get_real_user(self.runtime.anonymous_student_id).username,
            'user_email': self.runtime.get_real_user(self.runtime.anonymous_student_id).email,
        }

    def _past_due(self):
        """
        Return whether due date has passed.
        """
        due = get_extended_due_date(self)
        if due is not None:
            return self._now() > due
        return False

    @staticmethod
    def _now():
        """
        Get current date and time.
        """
        return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
