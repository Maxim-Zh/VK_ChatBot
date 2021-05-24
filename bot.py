#!/usr/bin/env python 3
import vk_api
import vk_api.bot_longpoll
import random
from my_token import token

group_id = 204762908


class Bot:
    def __init__(self, group_id, token):
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = vk_api.bot_longpoll.VkBotLongPoll(vk=self.vk, group_id=self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        for event in self.long_poller.listen():
            print('Получено событие')
            try:
                self.on_event(event=event)
            except Exception as exc:
                print(exc)

    def on_event(self, event):
        if event.type == vk_api.bot_longpoll.VkBotEventType.MESSAGE_NEW:
            print(f'Получено сообщение "{event.object.message["text"]}" '
                  f'от пользователя {event.object.message["from_id"]}')
            # print(event)
            self.api.messages.send(message=event.object.message["text"],
                                   random_id=random.randint(0, 2 ** 20),
                                   peer_id=event.object.message["peer_id"]
                                   )
        elif event.type == vk_api.bot_longpoll.VkBotEventType.MESSAGE_TYPING_STATE:
            print('Пользователь печатает...')


if __name__ == '__main__':
    bot = Bot(group_id=group_id, token=token)
    bot.run()
