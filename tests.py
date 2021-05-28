#!/usr/bin/env python 3
import settings
from unittest import TestCase
from unittest.mock import patch, Mock
from vk_api.bot_longpoll import VkBotMessageEvent
from pony.orm import db_session, rollback
from bot import Bot
from copy import deepcopy

from generate_ticket import generate_ticket


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()
    return wrapper


class Test(TestCase):
    RAW_EVENT = {'type': 'message_new', 'object':
                     {'message':
                          {'date': 1621943414, 'from_id': 17192721, 'id': 175, 'out': 0, 'peer_id': 17192721,
                           'text': 'Привет!', 'conversation_message_id': 164, 'fwd_messages': [], 'important': False,
                           'random_id': 0, 'attachments': [], 'is_hidden': False},
                      'client_info':
                          {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'callback',
                                              'intent_subscribe', 'intent_unsubscribe'],
                           'keyboard': True, 'inline_keyboard': True, 'carousel': True, 'lang_id': 3}},
                 'group_id': 204762908, 'event_id': '1c3f5ca24dec0aff3eb6185018fb649e701a0ada'}

    INPUTS = [
        'Привет',
        'Когда будет выставка?',
        'Где она пройдет?',
        'Зарегай меня',
        'Ма',
        'Максим',
        'maks@ma',
        'maks@maks.ru',
    ]

    EXPECTED_OUTPUTS = [
        settings.INTENTS[0]['answer'],
        settings.INTENTS[1]['answer'],
        settings.INTENTS[2]['answer'],
        settings.SCENARIOS['registration']['steps']['step_1']['text'],
        settings.SCENARIOS['registration']['steps']['step_1']['failure_text'],
        settings.SCENARIOS['registration']['steps']['step_2']['text'],
        settings.SCENARIOS['registration']['steps']['step_2']['failure_text'],
        settings.SCENARIOS['registration']['steps']['step_3']['text'].format(name='Максим', email='maks@maks.ru'),
    ]

    def test_run(self):
        count = 5
        obj = {}
        events = [obj] * count  # [obj, obj, ...]
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot(group_id='', token='')
                bot.on_event = Mock()
                bot.send_image = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(event=obj)
                assert bot.on_event.call_count == count

    @isolate_db
    def test_scenario(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot(group_id='', token='')
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()

        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])
        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_image_generator(self):
        with open(file='files/avatar_for_test.png', mode='rb') as avatar_test_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_test_file.read()

        with patch('requests.get', return_value=avatar_mock):
            ticket_file = generate_ticket(name='name', email='email@email.com')

        with open(file='files/ticket_for_test.png', mode='rb') as test_file:
            assert ticket_file.read() == test_file.read()
