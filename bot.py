#!/usr/bin/env python 3
import vk_api
import random
import logging
import handlers
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


class UserState:
    """
    UserState in Scenario
    """
    def __init__(self, scenario_name, scenario_step_name, context=None):
        self.scenario_name = scenario_name
        self.scenario_step_name = scenario_step_name
        self.context = context or {}


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
        self.user_id_states = dict()  # user_id(peer_id): UserState object

    def run(self):
        """Run Bot"""
        for event in self.long_poller.listen():
            try:
                self.on_event(event=event)
            except Exception:
                log.exception('Error in event processing')

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

        if user_id in self.user_id_states:
            text_to_send = self.continue_scenario(user_id=user_id, text=text)
        else:
            # search intent
            for intent in settings.INTENTS:
                log.debug(f'User gets intent - {intent["name"]}')
                if any(token in text.lower() for token in intent['tokens']):
                    if intent['answer']:
                        text_to_send = intent['answer']
                    else:
                        text_to_send = self.start_scenario(user_id=user_id, scenario_name=intent['scenario'])
                    break
            else:
                text_to_send = settings.DEFAULT_ANSWER

        self.api.messages.send(message=text_to_send,
                               random_id=random.randint(0, 2 ** 25),
                               peer_id=user_id
                               )

    def start_scenario(self, user_id, scenario_name):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        text_to_send = step['text']
        self.user_id_states[user_id] = UserState(scenario_name=scenario_name, scenario_step_name=first_step)
        return text_to_send

    def continue_scenario(self, user_id, text):
        current_user = self.user_id_states[user_id]
        steps = settings.SCENARIOS[current_user.scenario_name]['steps']
        step = steps[current_user.scenario_step_name]
        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=current_user.context):
            # next step
            next_step = steps[step['next_step']]
            text_to_send = next_step['text'].format(**current_user.context)
            if next_step['next_step']:
                # switch to next step
                current_user.scenario_step_name = step['next_step']
            else:
                # finish scenario
                log.info('User added to Database: {name} - {email}'.format(**current_user.context))
                self.user_id_states.pop(user_id)
        else:
            # retry
            text_to_send = step['failure_text'].format(**current_user.context)
        return text_to_send


if __name__ == '__main__':
    configure_logging()
    bot = Bot(group_id=settings.GROUP_ID, token=settings.TOKEN)
    bot.run()
