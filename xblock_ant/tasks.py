# coding=utf-8

from ifmo_celery_grader.tasks.helpers import GraderTaskBase, submit_task_grade, reserve_task

import json
import requests


class DelayedAntGraderTask(GraderTaskBase):
    """
    Проверяет тот факт, что пользователь действительно начал выполнение
    лабораторной.

    В действительности, эта штука, хоть и Грэйдер, но ничего не проверяет, а
    только в случае необходимости создаёт задание на проверку и ставит его в
    очередь.
    """

    def grade(self, student_input, grader_payload):
        """
        Ничего не проверяет по факту.
        """
        return {}

    def grade_success(self, student_input, grader_payload, system_payload, system, response):
        """
        Проводит валидацию состояния выполнения лабораторной работы,
        предоставляемою СУО. В том случае, если работа всё-таки началась, в
        очередь будет поставлена проверка задания.

        Эта штука выполняется каждый раз, когда пользователь нажал "Начать
        лабораторную работу", каждый раз в очередь ставятся новые задания со
        всеми вытекающими.

        TODO: Защитить от флуда
        """

        module = system.get('module')
        state = json.loads(module.state)

        # Стучимся до СУО, получаем статистику выполнения
        result = requests.get(grader_payload.get('attempts_url') % {
            'user_id': student_input.get('user_id'),
            'user_email': student_input.get('user_email'),
            'course_id': grader_payload.get('ant_course_id'),
            'unit_id': grader_payload.get('ant_unit_id')
        })

        # Получаем последнюю попытку, если таковая имело место
        attempts_data = json.loads(result.text)
        latest_attempt = attempts_data['attempts'][-1] if len(attempts_data['attempts']) > 0 else None

        # Если последняя попытка была, и она ещё не закончена
        if latest_attempt is not None and latest_attempt.get('end') is None:

            # Установим статус модуля в "Выполнение"
            state['ant_result'] = json.dumps(response)
            state['attempts'] = len(response['attempts'])
            state['ant_status'] = 'RUNNING'

            # Поставим в очередь задачу по проверке баллов
            new_task = reserve_task(None, save=True,
                                    grader_payload=grader_payload,
                                    system_payload=system_payload,
                                    student_input=student_input,
                                    task_type='ANT_CHECK_DELAYED')
            submit_ant_check(new_task)

        # В противном случае сбросим статус, чтобы не пугать пользователя
        # "подвисшей лабой"
        else:
            state['ant_status'] = 'IDLE'

        # Сохраняем всё, что наменяли
        module.state = json.dumps(state)
        module.save()


class AntCheckTask(GraderTaskBase):
    """
    Задание на вытягивание баллов и истории из СУО. Загружает статистику из
    СУО, проставляет баллы, записывает историю и всё такое.
    """

    def grade(self, student_input, grader_payload):

        # Просто стучимся по url, заданному api. Всю оценочную деятельность
        # студента уже проверила СУО.
        result = requests.get(grader_payload.get('attempts_url') % {
            'user_id': student_input.get('user_id'),
            'user_email': student_input.get('user_email'),
            'course_id': grader_payload.get('ant_course_id'),
            'unit_id': grader_payload.get('ant_unit_id')
        })
        return json.loads(result.text)

    def grade_success(self, student_input, grader_payload, system_payload, system, response):

        module = system.get('module')
        state = json.loads(module.state)

        # Приведём оценку за лабораторную к взвешенному значению и сохраним всё
        module.max_grade = float(100)
        module.grade = 0

        # Получаем последнюю попытку, если таковая была
        latest_attempt = response['attempts'][-1] if len(response['attempts']) > 0 else None

        # Если последняя попытка была (то есть как минимум одна попытка
        # сдачи)...
        if latest_attempt is not None:

            # ... запишем баллы, историю, количество попыток вцелом
            print latest_attempt
            module.grade = latest_attempt.get('result', 0)
            if module.grade is not None:
                state['score'] = module.grade / module.max_grade * grader_payload.get('max_score', 1)

            state['ant_result'] = json.dumps(response)
            state['attempts'] = len(response['attempts'])

            # Если времени окончания нет, то лабораторная ещё идёт
            state['ant_status'] = 'RUNNING' if latest_attempt.get('end') is None else 'IDLE'

            module.state = json.dumps(state)

        # ... в противном случае просто обнулим результат
        else:
            module.grade = 0

        module.save()

        # Если оказалось, что лабораторная всё ещё идёт, то просто создадим
        # плановую проверку. Через интервал равный веремени, отведённому на
        # лабораторную, вытянем баллы из СУО ещё раз, со всеми теми же
        # параметрами.
        if state['ant_status'] == 'RUNNING':
            new_task = reserve_task(None, save=True,
                                    grader_payload=grader_payload,
                                    system_payload=system_payload,
                                    student_input=student_input,
                                    task_type='ANT_CHECK')
            submit_ant_check(new_task)


def submit_delayed_ant_precheck(task):
    """
    Создаём отложенное задание. Подразумевается, что ровно через двадцать
    секунд после того, как пользователь нажал в LMS edX'а кнопку "Начать
    лабораторную", он начнёт выполнение лабораторной в СУО. К этому времени СУО
    сделает все необходимые изменения в себе, создаст ему "попытку" в своей
    базе и так далее. Вытягиваем баллы, а также информацию о том, что студент
    всё-таки начал прохождение лабораторной в СУО через этот магический
    промежуток времени.

    Подразумевается, что задание уже создано, которое должно иметь уникальный
    идентификатор, и мы просто ставим его в очередь.

    :param task: Сущность задания

    :return: Поставленное в очередь задание
    """
    return submit_task_grade(DelayedAntGraderTask, task, countdown=20)


def submit_ant_check(task, countdown=None):
    """
    Создаёт отложенное задание на проверку.

    Подразумевается, что задание уже создано, которое должно иметь уникальный
    идентификатор, и мы просто ставим его в очередь.

    :param task: Сущность задания
    :param countdown: Интервал, через который нужно выполнить проверку. По
                      умолчанию равен времени, отведённое на выполнение
                      лабораторной (задаётся в настройках лаборатороной в
                      студии)

    :return: Поставленное в очередь задание
    """
    if countdown is None:
        countdown = task.grader_payload.get('ant_time_limit')*60
    return submit_task_grade(AntCheckTask, task, countdown=countdown)


def _update_module_state(module, state):
    """
    Сохраняет состояние модуля.

    :param module: Модуль, чьё состояние нужно сохранить
    :param state: Новое состояние модуля (json)

    :return:
    """
    module.state = json.dumps(state)
    module.save()