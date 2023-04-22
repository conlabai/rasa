import argparse
import os
import time
import yaml
import asyncio

from sanic import Sanic, response

from rasa.shared.core.domain import Domain
from rasa.core.nlg import TemplatedNaturalLanguageGenerator
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.constants import ENV_SANIC_BACKLOG, DEFAULT_SANIC_WORKERS
from sanic.log import logger, logging
from aiohttp import ClientSession
from aiohttp_retry import RetryClient 

# from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.retry import Retry

DEFAULT_SERVER_PORT = 5056
DEFAULT_RESPONSE_NAME = "utter_default_response"
DEFAULT_RESPONSE = "Sorry, I didn't understand that."
CANNED_RESPONSES = {}
CANNED_RESPONSES_REFRESHED = 0
REFRESH_SECONDS = int(os.environ.get('NLG_CHATWOOT_REFRESH_SECONDS', 60))
DOMAIN = {}
DOMAIN_PATH = os.environ.get('NLG_DOMAIN_PATH', "")
DEBUG = os.environ.get('NLG_DEBUG', 'False').lower() in ('true', '1', 't')


def create_argument_parser():
    """Parse all the command line arguments for the nlg server script."""

    parser = argparse.ArgumentParser(description="starts the nlg endpoint")
    parser.add_argument(
        "-p",
        "--port",
        default=DEFAULT_SERVER_PORT,
        type=int,
        help="port to run the server at",
    )
    parser.add_argument(
        "--workers",
        default=DEFAULT_SANIC_WORKERS,
        type=int,
        help="Number of processes to spin up",
    )

    return parser


async def get_domain():
    """If local domain file is present, read that file. 
       Otherwise, Request domain file from Rasa."""
    if DOMAIN_PATH:
        with open(DOMAIN_PATH, "r") as stream:
            try:
                domain_yaml = yaml.safe_load(stream)
                logger.debug(f'Loaded domain from file {DOMAIN_PATH}:\n{domain_yaml}')
                return domain_yaml
            except yaml.YAMLError as exc:
                raise SystemExit(exc, f"Error reading domain from {DOMAIN_PATH}")

    rasa_url = os.environ.get("RASA_URL", "http://localhost:5005")
    rasa_token = os.environ.get("RASA_TOKEN", None)
    request_url = f'{rasa_url}/domain'
    headers = {"Accept": "application/json"}
    params = {}
    if rasa_token:
        params["token"] = rasa_token
    client_session = ClientSession()
    retry_client = RetryClient(client_session=client_session)
    async with retry_client.get(request_url, headers=headers, params=params) as response:
        domain = await response.json()
        logger.debug(f'Received domain from Rasa:\n{domain}')
        await client_session.close()
        return domain


async def refresh_responses():
    """Call chatwoot api to get canned responses and get the model domain data."""
    global CANNED_RESPONSES
    global CANNED_RESPONSES_REFRESHED
    global DOMAIN

    logger.info('Refreshing responses...')
    chatwoot_url = os.environ.get("CHATWOOT_URL", "http://localhost:3000")
    chatwoot_api_key = os.environ['CHATWOOT_API_KEY']
    request_url = f'{chatwoot_url}/api/v1/accounts/1/canned_responses'
    headers = {"Content-Type": "application/json", "api_access_token": chatwoot_api_key}
    client_session = ClientSession()
    retry_client = RetryClient(client_session=client_session)
    async with retry_client.get(request_url, headers=headers, raise_for_status=True) as response:
        responses = await response.json()
        CANNED_RESPONSES = {f'utter_{r["short_code"]}': [{'text': r['content']}] for r in responses}
        logger.debug(f'Refreshed CANNED_RESPONSES: {CANNED_RESPONSES}')
        DOMAIN = Domain.from_dict(await get_domain())
        logger.debug(f'Refreshed DOMAIN: {DOMAIN}')
        await client_session.close()

    CANNED_RESPONSES_REFRESHED = time.time()


async def generate_response(nlg_call):
    """Mock response generator.

    Generates the responses from canned responses or the bot's domain file.
    """

    kwargs = nlg_call.get("arguments", {})
    response = nlg_call.get("response")
    sender_id = nlg_call.get("tracker", {}).get("sender_id")
    events = nlg_call.get("tracker", {}).get("events")
    tracker = DialogueStateTracker.from_dict(sender_id, events, DOMAIN.slots)
    channel_name = nlg_call.get("channel")

    logger.info(f'Generating message for response: {response}')

    if not CANNED_RESPONSES or not DOMAIN or time.time() - CANNED_RESPONSES_REFRESHED > REFRESH_SECONDS:
        await refresh_responses()

    message = await TemplatedNaturalLanguageGenerator(CANNED_RESPONSES).generate(
        response, tracker, channel_name, **kwargs)
    if message:
        logger.info(f'Returning canned response: {message}')
        return message

    message = await TemplatedNaturalLanguageGenerator(DOMAIN.responses).generate(
        response, tracker, channel_name, **kwargs
    )
    if message:
        logger.info(f'Returning domain response: {message}')
        return message

    default_response = await TemplatedNaturalLanguageGenerator(CANNED_RESPONSES).generate(
        DEFAULT_RESPONSE_NAME, tracker, channel_name, **kwargs)
    if default_response:
        logger.info(f'Returning canned default response {default_response}')
        return default_response

    default_response = await TemplatedNaturalLanguageGenerator(DOMAIN.responses).generate(
        DEFAULT_RESPONSE_NAME, tracker, channel_name, **kwargs)
    if default_response:
        logger.info(f'Returning default domain response {default_response}')
        return default_response
        
    logger.info(f'Returning built-in default response {DEFAULT_RESPONSE}')
    return {"text": DEFAULT_RESPONSE}


def run_server(port, workers):
    app = Sanic("nlg_server")
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    @app.route("/nlg", methods=["POST", "OPTIONS"])
    async def nlg(request):
        """Endpoint which processes the Core request for a bot response."""
        nlg_call = request.json
        bot_response = await generate_response(nlg_call)

        return response.json(bot_response)
        return None

    app.run(
        host="0.0.0.0",
        port=port,
        workers=workers,
        backlog=int(os.environ.get(ENV_SANIC_BACKLOG, "100")),
        debug=DEBUG,
        auto_reload=os.environ.get('NLG_AUTO_RELOAD', False),
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

    # Running as standalone python application
    arg_parser = create_argument_parser()
    cmdline_args = arg_parser.parse_args()
    asyncio.run(refresh_responses())

    run_server(cmdline_args.port, cmdline_args.workers)

# flake8: noqa E501