from unittest import TestCase
from unittest.mock import patch, Mock, ANY
from vk_api.bot_longpoll import VkBotMessageEvent

from bot import Bot


class Test(TestCase):
    RAW_EVENT = {'type': 'message_new', 'object':
                     {'message':
                          {'date': 1621943414, 'from_id': 17192721, 'id': 175, 'out': 0, 'peer_id': 17192721,
                           'text': 'k', 'conversation_message_id': 164, 'fwd_messages': [], 'important': False,
                           'random_id': 0, 'attachments': [], 'is_hidden': False},
                      'client_info':
                          {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'callback',
                                              'intent_subscribe', 'intent_unsubscribe'],
                           'keyboard': True, 'inline_keyboard': True, 'carousel': True, 'lang_id': 3}},
                 'group_id': 204762908, 'event_id': '1c3f5ca24dec0aff3eb6185018fb649e701a0ada'}

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
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(event=obj)
                assert bot.on_event.call_count == count

    def test_on_event(self):
        event = VkBotMessageEvent(raw=self.RAW_EVENT)

        send_mock = Mock()

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll'):
                bot = Bot('', '')
                bot.api = Mock()
                bot.api.messages.send = send_mock

                bot.on_event(event=event)

        send_mock.assert_called_once_with(message='Сам ты ' + self.RAW_EVENT['object']['message']['text'],
                                          random_id=ANY,
                                          peer_id=self.RAW_EVENT['object']['message']['peer_id']
                                          )
