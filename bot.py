#!/usr/bin/env python 3
import requests
import vk_api
import random
import logging
import handlers
from pony.orm import db_session
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from models import UserState, Registration

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
    Registration Bot for vk.com

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

    @db_session
    def on_event(self, event):
        """
        Chatting with user
        :param event: VkBotMessageEvent object
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info(f"Can't process this - {event.type}")
            return

        user_id = event.object.message["peer_id"]
        text = event.object.message["text"]
        current_user_state = UserState.get(user_id=str(user_id))

        if current_user_state is not None:
            self.continue_scenario(text=text, current_user_state=current_user_state, user_id=user_id)
        else:
            # search intent
            for intent in settings.INTENTS:
                log.debug(f'User gets intent - {intent["name"]}')
                if any(token in text.lower() for token in intent['tokens']):
                    if intent['answer']:
                        self.send_text(text_to_send=intent['answer'], user_id=user_id)
                    else:
                        self.start_scenario(user_id=user_id, scenario_name=intent['scenario'], text=text)
                    break
            else:
                self.send_text(text_to_send=settings.DEFAULT_ANSWER, user_id=user_id)

    def send_text(self, text_to_send, user_id):
        self.api.messages.send(message=text_to_send,
                               random_id=random.randint(0, 2 ** 25),
                               peer_id=user_id
                               )

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_info = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_info = self.api.photos.saveMessagesPhoto(**upload_info)
        owner_id = image_info[0]['owner_id']
        media_id = image_info[0]['id']
        attachment = f'photo{owner_id}_{media_id}'
        self.api.messages.send(attachment=attachment,
                               random_id=random.randint(0, 2 ** 25),
                               peer_id=user_id
                               )

    def what_to_send(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(text_to_send=step['text'].format(**context), user_id=user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text=text, context=context)
            self.send_image(image=image, user_id=user_id)

    def start_scenario(self, user_id, scenario_name, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.what_to_send(step=step, user_id=user_id, text=text, context={})
        UserState(user_id=str(user_id), scenario_name=scenario_name, scenario_step_name=first_step, context={})

    def continue_scenario(self, text, current_user_state, user_id):
        steps = settings.SCENARIOS[current_user_state.scenario_name]['steps']
        step = steps[current_user_state.scenario_step_name]
        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=current_user_state.context):
            # next step
            next_step = steps[step['next_step']]
            self.what_to_send(step=next_step, user_id=user_id, text=text, context=current_user_state.context)
            if next_step['next_step']:
                # switch to next step
                current_user_state.scenario_step_name = step['next_step']
            else:
                # finish scenario
                log.info('User added to Database: {name} - {email}'.format(**current_user_state.context))
                Registration(name=current_user_state.context['name'], email=current_user_state.context['email'])
                current_user_state.delete()
        else:
            # retry
            self.send_text(text_to_send=step['failure_text'].format(**current_user_state.context), user_id=user_id)


if __name__ == '__main__':
    configure_logging()
    bot = Bot(group_id=settings.GROUP_ID, token=settings.TOKEN)
    bot.run()
