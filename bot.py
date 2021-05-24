#!/usr/bin/env python 3
import vk_api
from vk_api import bot_longpoll
from my_token import token

group_id = 204762908


class Bot:
    def __init__(self, group_id, token):
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = bot_longpoll.VkBotLongPoll(self.vk, self.group_id)

    def run(self):
        pass


if __name__ == '__main__':
    bot = Bot(group_id=group_id, token=token)
    bot.run()
