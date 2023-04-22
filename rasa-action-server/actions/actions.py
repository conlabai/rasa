# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import os
from typing import Any, Text, Dict, List
import datetime

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# import requests
import logging
from aiohttp import ClientSession


# logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

def is_working_time():
    now = datetime.datetime.now().time()

    # 10:00 MSK - 22:00 MSK in UTC
    start_time = datetime.datetime.strptime("07:00", "%H:%M").time()
    end_time = datetime.datetime.strptime("19:00", "%H:%M").time()

    if start_time <= now <= end_time:
        return True
    else:
        return False


# send request to chatwoot
async def chatwoot_request(url: str, method: str = 'post', payload: Dict = None) -> Dict:
    token = os.environ["CHATWOOT_API_KEY"]
    chatwoot_url = os.environ["CHATWOOT_URL"]
    url = f'{chatwoot_url}/api/v1{url}'

    headers = {
        'Content-Type': "application/json",
        'api_access_token': token
    }
    async with ClientSession(headers=headers, raise_for_status=True) as session: 
        if method == 'post':
            response = await session.post(url=url, json=payload, headers=headers)
        else:
            response = await session.get(url=url, headers=headers)

        async with response:
            logging.info(f'chatwoot request ->: {method} {response.url} {payload}')
            data = await response.json()
            logging.info(f'chatwoot response <-: {response.status} {data}')
            return data


# send get request to chatwoot
async def chatwoot_get(url: str) -> Dict:
    return await chatwoot_request(method='get', url=url)


# send post request to chatwoot
async def chatwoot_post(url: str, payload: Dict) -> Dict:
    return await chatwoot_request(method='post', url=url, payload=payload)


# change conversation status to open
async def chatwoot_open_conversation(conversation_id: int, account_id: int) -> Dict:
    url = f'/accounts/{account_id}/conversations/{conversation_id}/toggle_status'
    payload = {"status": "open"}
    response = await chatwoot_post(url=url, payload=payload)
    logging.debug(f'chatwoot_open_conversation url: {url} payload: {payload} ->: {response}')
    return response['payload']


# get conversation labels
async def chatwoot_get_conversation_labels(conversation_id: int, account_id: int) -> Dict:
    url = f'/accounts/{account_id}/conversations/{conversation_id}/labels'
    response = await chatwoot_get(url=url)
    return response['payload']


# set conversation labels
async def chatwoot_label_conversation(labels: List, conversation_id: int,
                                      account_id: int) -> Dict:
    url = f'/accounts/{account_id}/conversations/{conversation_id}/labels'
    payload = {"labels": labels}
    response = await chatwoot_post(url=url, payload=payload)
    logging.debug(f'chatwoot_label_conversation url: {url} payload: {payload} ->: {response}')
    return response['payload']


def get_chatwoot_metadata(metadata):

    logging.debug(f'get_chatwoot_metadata ->: {metadata}')

    if not metadata:
        return (None, None)

    account_id: str = None
    conversation_id: str = None

    if metadata.get('account', None):  # we are not in a chatwoot conversation
        account_id = metadata['account']['id']

    if metadata.get('conversation', None):  # we are not in a chatwoot conversation
        conversation_id = metadata['conversation']['id']

    return (account_id, conversation_id)


# test action
class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Hello World!")

        return []


# label conversation
class ActionTagConversation(Action):

    def name(self) -> Text:
        return "action_tag_conversation"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        logging.info('ActionTagConversation')

        metadata = tracker.latest_message['metadata']
        (account_id, conversation_id) = get_chatwoot_metadata(metadata)

        if account_id and conversation_id:
            chatwoot_labels = await chatwoot_get_conversation_labels(conversation_id, account_id)
            rasa_labels = [tracker.get_intent_of_latest_message(skip_fallback_intent=False)]
            await chatwoot_label_conversation(chatwoot_labels + rasa_labels, conversation_id, account_id)

        return []


# change conversation status to open
class ActionHandoff(Action):

    def name(self) -> Text:
        return "action_handoff"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        logging.info('ActionHandoff')

        metadata = tracker.latest_message['metadata']

        (account_id, conversation_id) = get_chatwoot_metadata(metadata)

        if account_id and conversation_id:
            await chatwoot_open_conversation(conversation_id, account_id)

        return []

# Use handoff notification template in dependance of working hours
class ActionHandoffNotification(Action):

    def name(self) -> Text:
        return "action_handoff_notification"

    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
       
        if is_working_time():
            dispatcher.utter_message(response="utter_handoff_is_working_time")
        else:
            dispatcher.utter_message(response="utter_handoff_out_of_office")
        return []

# Executes the fallback action and handoff
class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback_and_handoff"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        logging.info('ActionDefaultFallback')

        if is_working_time():
            dispatcher.utter_message(response="utter_handoff_is_working_time")
        else:
            dispatcher.utter_message(response="utter_handoff_out_of_office")

        metadata = tracker.latest_message['metadata']

        (account_id, conversation_id) = get_chatwoot_metadata(metadata)

        if account_id and conversation_id:
            await chatwoot_open_conversation(conversation_id, account_id)

        return []

# flake8: noqa: E501