# -*- coding: utf-8 -*-

from celery.states import PENDING
from xblock.core import XBlock
from xblock.fragment import Fragment
from xmodule.util.duedate import get_extended_due_date
from webob.exc import HTTPFound, HTTPForbidden, HTTPOk, HTTPInternalServerError

import datetime
import json
import pytz
import requests

from xblock_ant.utils import resource_string, render_template
from xblock_ant.ant_xblock_fields import AntXBlockFields
from xblock_ant.tasks import submit_delayed_ant_precheck, submit_ant_check, reserve_task
from xblock_ant.settings import CONFIGURATION as CONFIG


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
        fragment.add_css(self._get_resource('static/css/student_view_style.css'))
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
                'weight': self.weight,
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
            'score': round(self.score, 2),
            'total': self.weight,
        }

    def max_score(self):
        """
        Максимально возможный балл за лабораторную.

        :return:
        """
        return self.weight

    @XBlock.handler
    def start_lab(self, request, suffix=''):
        """
        Начало выполнение лабораторной.

        Вызывается, когда пользователь нажал кнопку "Начать лабораторную".

        :param request:
        :param suffix:

        :return:
        """

        from ifmo_celery_grader.models import GraderTask
        # Проверим лабораторную на ошибки конфигурации
        has_errors, data_obj = self._validate_lab_config()
        if has_errors:
            return HTTPInternalServerError(json=data_obj)

        # Начинаем лабораторную только в том случае, если срок не истёк
        if self._past_due():
            return HTTPForbidden(json={"result": "error", "message": "Past due"})

        # Собираем мета-данные для блока
        lab_meta = {
            'user_id': self.runtime.get_real_user(self.runtime.anonymous_student_id).id,
            'user_login': self.runtime.get_real_user(self.runtime.anonymous_student_id).username,
            'user_email': self.runtime.get_real_user(self.runtime.anonymous_student_id).email,
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
        # чем показывать ему лабораторную; делаем это в том случае, если есть
        # url для регистрации в конфигурации.
        register_url = CONFIG.get('REGISTER_URL')
        if register_url is not None:
            register_url = register_url % lab_meta
            requests.post(register_url)

        # Делаем редирект на страницу с лабораторной
        lab_url = self.lab_url % lab_meta
        return HTTPFound(location=lab_url)

    @XBlock.handler
    def check_lab_external(self, request, suffix=''):
        return HTTPOk(json=self._check_lab(request.GET))

    @XBlock.json_handler
    def get_course_info(self, data, suffix=''):
        # assert self._is_staff()
        t = requests.get(CONFIG.get('COURSE_INFO') % data)
        return t.text

    @XBlock.json_handler
    def check_lab(self, data, suffix=''):
        return self._check_lab(data)

    def _check_lab(self, data):
        """
        Проверить лабораторную работу.

        Вызывается, когда пользователь нажал кнопку "Проверить лабораторную".

        :param data:
        :return:
        """

        # Если в конфигурации лабораторной ошибки -- вообще ничего не делаем
        has_errors, data_obj = self._validate_lab_config()
        if has_errors:
            return data_obj

        # Проверяем лабораторную только в том случае, если срок не истёк
        if self._past_due():
            return {
                "result": "error",
                "message": "Время, отведённое на лабораторную работу, истекло.",
            }

        need_save, student_input = (True, self._get_student_input()) if data.get('user_login') is None else \
            (False, self._get_student_input_no_auth(username=data.get('user_login')))
        if not student_input:
            return {
                "result": "error",
                "message": "Не удалось определить пользователя для проверки",
            }

        # Предварительно проверим наличие модуля, чтобы не инициировать
        # проверку для несуществующего.
        from courseware.models import StudentModule
        try:
            StudentModule.objects.get(module_state_key=self.location,
                                      student__username=student_input.get('user_login'))
        except StudentModule.DoesNotExist:
            return {
                'state': "Модуль для указанного пользователя не существует."
            }

        task = reserve_task(self if need_save else None,
                            grader_payload=self._get_grader_payload(),
                            system_payload=self._get_system_payload(student_input.get('user_id')),
                            student_input=student_input,
                            save=need_save,
                            task_type='ANT_CHECK')
        submit_ant_check(task, countdown=0)
        return {
            "result": "success",
            "message": "Лабораторная работа поставлена в очередь на проверку.",
        }

    @XBlock.json_handler
    def save_settings(self, data, suffix=''):
        """
        Сохранить настройки XBlock'а.

        :param data:
        :param suffix:
        :return:
        """
        # assert self._is_staff()
        self.display_name = data.get('display_name')
        self.weight = data.get('weight')
        self.ant_course_id = data.get('course_id', '')
        self.ant_unit_id = data.get('unit_id', '')
        self.content = data.get('content', '')
        self.ant_time_limit = data.get('time_limit', 0)
        self.ant_attempts_limit = data.get('attempts_limit', 0)
        self.attempts_url = data.get('attempts_url').strip() or None
        self.lab_url = data.get('lab_url').strip() or None
        return '{}'

    @XBlock.json_handler
    def reset_user_data(self, data, suffix=''):
        assert self._is_staff()
        from courseware.models import StudentModule
        user_login = data.get('user_login')
        try:
            module = StudentModule.objects.get(module_state_key=self.location,
                                               student__username=user_login)
            module.state = '{}'
            module.max_grade = None
            module.grade = None
            module.save()
            return {
                'state': "Состояние пользователя сброшено.",
            }
        except StudentModule.DoesNotExist:
            return {
                'state': "Модуль для указанного пользователя не существует."
            }

    @XBlock.json_handler
    def get_user_data(self, data, suffix=''):
        """
        Получить состояние определённого пользователя.

        :param data:
        :param suffix:
        :return:
        """
        assert self._is_staff()
        from courseware.models import StudentModule
        user_login = data.get('user_login')
        try:
            module = StudentModule.objects.get(module_state_key=self.location,
                                               student__username=user_login)
            return {
                'state': module.state,
            }
        except StudentModule.DoesNotExist:
            return {
                'state': "Модуль для указанного пользователя не существует."
            }

    def save_now(self):
        """
        Сохранить модуль в обход транзакций.

        :return:
        """
        self.save()

    @XBlock.json_handler
    def get_current_user_data(self, data, suffix=''):
        return self._get_student_context()

    @XBlock.handler
    def get_tasks_data(self, data, suffix=''):
        assert self._is_staff()
        from ifmo_celery_grader.models import GraderTask
        grader_tasks = GraderTask.objects.filter(module_id=self.location)
        tasks = [['id', 'task_id', 'student_input', 'grader_payload', 'system_payload', 'task_input', 'task_output',
                  'course_id', 'module_id', 'user_target.username', 'task_type', 'task_state']]
        for task in grader_tasks:
            tasks.append([
                task.id,
                task.task_id,
                task.student_input,
                task.grader_payload,
                task.system_payload,
                task.task_input,
                task.task_output,
                task.course_id,
                task.module_id,
                task.user_target.username if task.user_target is not None else None,
                task.task_type,
                task.task_state,
            ])
        return HTTPOk(
            body="\n".join(["\t".join(["" if j is None else str(j) for j in i]) for i in tasks]),
            headers={
                'Content-Disposition': 'attachment; filename=tasks_%s.tsv' % self.scope_ids.usage_id.block_id,
                'Content-Type': 'text/tab-separated-values'
            })

    @XBlock.handler
    def get_grades_data(self, data, suffix=''):
        assert self._is_staff()
        from courseware.models import StudentModule
        grades_objects = StudentModule.objects.filter(module_state_key=self.location)
        grades = [['id', 'username', 'score', 'max_grade', 'state', 'created', 'modified']]
        for grade in grades_objects:
            grades.append([
                grade.id,
                grade.student.username if grade.student is not None else None,
                grade.grade,
                grade.max_grade,
                grade.state,
                grade.created,
                grade.modified,
            ])
        return HTTPOk(
            body="\n".join(["\t".join(["" if j is None else str(j) for j in i]) for i in grades]),
            headers={
                'Content-Disposition': 'attachment; filename=grades_%s.tsv' % self.scope_ids.usage_id.block_id,
                'Content-Type': 'text/tab-separated-values'
            })

    def _get_student_context(self):
        """
        Получить контекст текущего пользователя для отображения шаблона.
        :return:
        """
        data = {
            'id': self.scope_ids.usage_id.block_id,
            'student_state': json.dumps(
                {
                    'score': {
                        'earned': round(self.score, 2) if self.score is not None else 0,
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
            'attempts_limit':
                self.attempts > self.ant_attempts_limit or
                self.attempts == self.ant_attempts_limit and self.ant_status != 'RUNNING',
        }

        if self._is_staff():
            data.update({
                # Debug window info
                'location': str(self.location),
                'ant_course_id':  self.ant_course_id,
                'ant_unit_id':  self.ant_unit_id,
                'ant_limit':  self.ant_attempts_limit,
                'lab_url': self.lab_url,
                'attempts_url': self.attempts_url,
                'weight': self.weight,
               
                # This is probably studio, find out some more ways to determine this
                'is_studio': self.runtime.get_real_user is None,
                # 'tasks':tasks

                # URL-ы для внешней работы с блоком, вынесены сюда, поскольку
                # js-runtime не генерируют схему, а этот -- да.
                'check_no_auth':
                    self.runtime.handler_url(self, 'check_lab_external', thirdparty=True),
                'get_tasks_data':
                    self.runtime.handler_url(self, 'get_tasks_data', thirdparty=True).replace('_noauth', ''),
                'get_grades_data':
                    self.runtime.handler_url(self, 'get_grades_data', thirdparty=True).replace('_noauth', ''),
            })
        return data

    @staticmethod
    def _get_resource(file_name):
        """
        Получить содержимое файла из ресурсов.

        :param file_name: Имя файла

        :return: Содержимое
        """
        return resource_string(file_name, package_name='xblock_ant')

    @staticmethod
    def _render_template(template_name, context=None):
        """
        Отрендерить шаблон.

        :param template_name: Имя шаблона
        :param context: Контекст для отображения

        :return: Содержимое
        """
        return render_template(template_name, context=context, package_name='xblock_ant')

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

    def _get_system_payload(self, user_id=None):
        """
        Данные, позволяющие идентифицировать сам модуль.

        :return:
        """
        return {
            'user_id': self.scope_ids.user_id if user_id is None else user_id,
            'course_id': unicode(self.course_id),
            'module_id': unicode(self.location),
            'max_score': self.weight,
        }

    def _get_student_input(self):
        """
        Пользовательский ввод.

        :return:
        """
        real_user = self.runtime.get_real_user(self.runtime.anonymous_student_id)
        if real_user is None:
            return None
        return {
            'user_id': real_user.id,
            'user_login': real_user.username,
            'user_email': real_user.email,
        }

    def _get_student_input_no_auth(self, username=None):
        from django.contrib.auth.models import User
        if username is None:
            return None
        else:
            try:
                u = User.objects.get(username=username)
                return {
                    'user_id': u.id,
                    'user_login': u.username,
                    'user_email': u.email,
                }
            except User.DoesNotExist:
                return None

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

    def _validate_lab_config(self):
        """
        Проверка лабораторной на ошибки.

        Сейчас проверяет только наличие unit_id и course_id.

        :return: (has_errors, data_obj) -- признак ошибки и объект с данными, чтобы вернуть в HTTPResponse
        """
        has_errors = any(map(lambda x: x in [0, None, ''], [self.ant_unit_id, self.ant_course_id, ]))
        data_obj = {
            'result': 'ok' if not has_errors else 'error',
        }
        if has_errors:
            data_obj['message'] = 'Improperly configured'
        return has_errors, data_obj

    def _is_staff(self):
        return getattr(self.xmodule_runtime, 'user_is_staff', False)
