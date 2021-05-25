#!/usr/bin/env python 3
import vk_api
import random
import logging
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from my_token import token

group_id = 204762908
log = logging.getLogger(name='bot_logger')
log.setLevel(level=logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s'))
log.addHandler(stream_handler)



class Bot:
    def __init__(self, group_id, token):
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(vk=self.vk, group_id=self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        for event in self.long_poller.listen():
            try:
                self.on_event(event=event)
            except Exception:
                log.exception('Ошибка в обработке события')

    def on_event(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            log.info(f'Получено сообщение "{event.object.message["text"]}" '
                  f'от пользователя {event.object.message["from_id"]}')
            self.api.messages.send(message='Сам ты ' + event.object.message["text"],
                                   random_id=random.randint(0, 2 ** 25),
                                   peer_id=event.object.message["peer_id"]
                                   )
        elif event.type == VkBotEventType.MESSAGE_TYPING_STATE:
            log.info(f'Пользователь {event.object["from_id"]} печатает...')
        else:
            log.debug(f'Я пока не умею это обрабатывать - {event.type}')


if __name__ == '__main__':
    bot = Bot(group_id=group_id, token=token)
    bot.run()
