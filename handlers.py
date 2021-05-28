#!/usr/bin/env python 3
"""
Handler - функция, принимающая на вход text (текст входящего сообщения) и context (dict, информация,
собранная в ходе сценария), возвращает bool: True, если шаг пройден, False - если данные введены неправильно.
"""
import re

from generate_ticket import generate_ticket

re_name = re.compile(pattern=r'^[\w\-\s]{3,30}$')
re_email = re.compile(pattern=r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b')


def handle_name(text, context):
    match = re.match(pattern=re_name, string=text)
    if match:
        context['name'] = text
        return True
    else:
        return False


def handle_email(text, context):
    matches = re.findall(pattern=re_email, string=text)
    if len(matches) > 0:
        context['email'] = matches[0]
        return True
    else:
        return False


def handle_generate_ticket(text, context):
    return generate_ticket(name=context['name'], email=context['email'])
