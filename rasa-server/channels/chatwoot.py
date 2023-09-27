import logging
from copy import deepcopy
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from typing import Dict, Text, Any, List, Optional, Callable, Awaitable

from rasa.core.channels.channel import InputChannel, UserMessage, OutputChannel
from rasa.shared.constants import INTENT_MESSAGE_PREFIX
from rasa.shared.core.constants import USER_INTENT_RESTART
from rasa.shared.exceptions import RasaException
from rasa.utils.endpoints import EndpointConfig, ClientResponseError

logger = logging.getLogger(__name__)


class ChatwootOutput(OutputChannel):
    """Output channel for Chatwoot."""

    # skipcq: PYL-W0236
    @classmethod
    def name(cls) -> Text:
        return "chatwoot"

    def __init__(self, endpoint: EndpointConfig, account_id: Text, conversation_id: Text) -> None:
        logger.debug(f'Initialising output channel {__name__} with url: {endpoint.url}')
        self.callback_endpoint = endpoint
        self.account_id = account_id
        self.conversation_id = conversation_id
        super().__init__()

    async def send_message(self, recipient_id: Text, text: Text, reply_markup: Dict = None) -> None:
        path = f'/api/v1/accounts/{self.account_id}/conversations/{self.conversation_id}'
        logger.debug(f'send_message: recipient_id: {recipient_id}, text: {text}, reply_markup: {reply_markup}, path: {path}')
        try:
            # await self.callback_endpoint.request(
            #     "post", content_type="application/json", subpath=f'{path}/toggle_typing_status?typing_status=on'
            # )
            if reply_markup:
                payload = reply_markup
            else:
                payload = {'content': text}
            await self.callback_endpoint.request(
                "post", content_type="application/json", subpath=f'{path}/messages', 
                json=payload
            )
            # await self.callback_endpoint.request(
            #     "post", content_type="application/json", subpath=f'{path}/toggle_typing_status?typing_status=off'
            # )
        except ClientResponseError as e:
            logger.error(
                "Failed to send output message to callback. "
                "Status: {} Response: {}"
                "".format(e.status, e.text)
            )

    async def send_text_message(
        self, recipient_id: Text, text: Text, **kwargs: Any
    ) -> None:
        """Sends text message."""
        for message_part in text.strip().split("\n\n"):
            await self.send_message(recipient_id, message_part)

    async def send_image_url(
        self, recipient_id: Text, image: Text, **kwargs: Any
    ) -> None:
        """Sends an image."""
        await self.send_photo(recipient_id, image)

    async def send_text_with_buttons(
        self,
        recipient_id: Text,
        text: Text,
        buttons: List[Dict[Text, Any]],
        button_type: Optional[Text] = "inline",
        **kwargs: Any,
    ) -> None:
        """Sends a message with an input selection.

        For more information: https://www.chatwoot.com/docs/product/others/interactive-messages

        :button_type: only inline

        """
        logger.debug(f'Generating button message, text: {text}, button_type: {button_type}, buttons: {buttons}')
        if button_type != "inline":
            logger.error(
                "Trying to send text with buttons for unknown "
                "button type {}".format(button_type)
            )
            return
# {
#     "content": "Select one of the items below",
#     "content_type": "input_select",
#     "content_attributes": {
#         "items": [
#             { "title": "Option1", "value": "Option 1" },
#             { "title": "Option2", "value": "Option 2" }
#         ]
#     },
#     "private":false
# }

        reply_markup = {
            "content": text,
            "content_type": "input_select",
            "content_attributes": {
                "items": [{'title': btn['title'], 'value': btn['payload']} for btn in buttons]
            },
            "private": False
        }

        await self.send_message(recipient_id, "", reply_markup=reply_markup)

    async def send_custom_json(
        self, recipient_id: Text, json_message: Dict[Text, Any], **kwargs: Any
    ) -> None:
        """Sends a message with a custom json payload."""
        json_message = deepcopy(json_message)

        recipient_id = json_message.pop("chat_id", recipient_id)

        send_functions = {
            ("text",): "send_message",
            ("photo",): "send_photo",
            ("audio",): "send_audio",
            ("document",): "send_document",
            ("sticker",): "send_sticker",
            ("video",): "send_video",
            ("video_note",): "send_video_note",
            ("animation",): "send_animation",
            ("voice",): "send_voice",
            ("media",): "send_media_group",
            ("latitude", "longitude", "title", "address"): "send_venue",
            ("latitude", "longitude"): "send_location",
            ("phone_number", "first_name"): "send_contact",
            ("game_short_name",): "send_game",
            ("action",): "send_chat_action",
            (
                "title",
                "decription",
                "payload",
                "provider_token",
                "start_parameter",
                "currency",
                "prices",
            ): "send_invoice",
        }

        for params in send_functions.keys():
            if all(json_message.get(p) is not None for p in params):
                args = [json_message.pop(p) for p in params]
                api_call = getattr(self, send_functions[params])
                await api_call(recipient_id, *args, **json_message)


class ChatwootInput(InputChannel):
    """Chatwoot input channel"""

    @classmethod
    def name(cls) -> Text:
        return "chatwoot"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        credentials.update({
            'headers': {
                'Content-Type': 'application/json',
                'api_access_token': credentials.get('api_access_token')
            }
        })
        return cls(EndpointConfig.from_dict(credentials))

    def __init__(self, endpoint: EndpointConfig) -> None:
        logger.debug(f'Initialising input channel {__name__} with config: {vars(endpoint)}')
        self.callback_endpoint = endpoint
        self.debug_mode = False

    @staticmethod
    def _is_valid_chatwoot_event(event: Dict[Text, Any]) -> bool:
        try:
            message_type = event.get('message_type')
            event_type = event.get('event')
            status = event.get('conversation',{}).get('status')
            return (message_type == "incoming" and event_type == "message_created"
                    and status == "pending")
        except Exception as e:
            logger.error(f"Invalid chatwoot event received, exception: {e}")
            return False

    def get_metadata(self, request: Request) -> Optional[Dict[Text, Any]]:
        """Extracts additional information from the incoming request.
         Implementing this function is not required. However, it can be used to extract
         metadata from the request. The return value is passed on to the
         ``UserMessage`` object and stored in the conversation tracker.
        Args:
            request: incoming request with the message of the user
        Returns:
            Metadata which was extracted from the request.
        """
        event = request.json
        return { 
            'conversation': event.get('conversation'),
            'account' : event.get('account')
        }

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> Blueprint:
        chatwoot_webhook = Blueprint("chatwoot_webhook", __name__)


        @chatwoot_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @chatwoot_webhook.route("/webhook", methods=["POST"])
        async def message(request: Request) -> Any:

            event = request.json
            logger.debug(f'event received: {event}')
            if not self._is_valid_chatwoot_event(event):
                return response.text("Skipped invalid event") 

            text = event.get('content')
            sender_id = event.get('sender').get('id')
            metadata = self.get_metadata(request)

            account_id = metadata.get('account').get('id')
            conversation_id = metadata.get('conversation').get('id')

            out_channel = ChatwootOutput(self.callback_endpoint, account_id, conversation_id)

            try:
                if text == (INTENT_MESSAGE_PREFIX + USER_INTENT_RESTART):
                    await on_new_message(
                        UserMessage(
                            text,
                            out_channel,
                            sender_id,
                            input_channel=self.name(),
                            metadata=metadata,
                        )
                    )
                    await on_new_message(
                        UserMessage(
                            "/start",
                            out_channel,
                            sender_id,
                            input_channel=self.name(),
                            metadata=metadata,
                        )
                    )
                else:
                    await on_new_message(
                        UserMessage(
                            text,
                            out_channel,
                            sender_id,
                            input_channel=self.name(),
                            metadata=metadata,
                        )
                    )
            except Exception as e:
                logger.error(f"Exception when trying to handle message.{e}")
                logger.debug(e, exc_info=True)
                if self.debug_mode:
                    raise
                pass

            return response.text("success")
        
        return chatwoot_webhook

# flake8: noqa: E501