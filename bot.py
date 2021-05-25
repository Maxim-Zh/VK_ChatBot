#!/usr/bin/env python 3
import vk_api
import random
import logging
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
try:
    import settings
except ImportError:
    exit('Copy settings.py.default to settings.py and set GROUP_ID and TOKEN')

log = logging.getLogger(name='bot_logger')


def configure_logging():
    log.setLevel(level=logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(fmt='%(levelname)s - %(message)s'))
    stream_handler.setLevel(level=logging.INFO)

    file_handler = logging.FileHandler(filename='bot_logger.log', mode='a', encoding='UTF-8', delay=False)
    file_handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s',
                                                datefmt='%d-%m-%Y %H:%M:%S')
                              )
    file_handler.setLevel(level=logging.DEBUG)

    log.addHandler(stream_handler)
    log.addHandler(file_handler)


class Bot:
    """
    Echo bot for vk.com

    Use Python 3.9
    """
    def __init__(self, group_id, token):
        """
        :param group_id: group id @ vk.com
        :param token: secret token
        """
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(vk=self.vk, group_id=self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        """Run Bot"""
        for event in self.long_poller.listen():
            try:
                self.on_event(event=event)
            except Exception:
                log.exception('Error in event processing')

    def on_event(self, event: VkBotEventType):
        """
        Send message back
        :param event:
        :return: None
        """
        if event.type == VkBotEventType.MESSAGE_NEW:
            log.debug(f'Got message "{event.object.message["text"]}" '
                      f'from user id {event.object.message["from_id"]}'
                      )
            self.api.messages.send(message='Сам ты ' + event.object.message["text"],
                                   random_id=random.randint(0, 2 ** 25),
                                   peer_id=event.object.message["peer_id"]
                                   )
        elif event.type == VkBotEventType.MESSAGE_TYPING_STATE:
            log.debug(f'User {event.object["from_id"]} typing...')
        else:
            log.info(f"Can't process this- {event.type}")


if __name__ == '__main__':
    configure_logging()
    bot = Bot(group_id=settings.GROUP_ID, token=settings.TOKEN)
    bot.run()
