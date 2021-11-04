import logging
import requests
import six
import random

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name, is_request_type

from typing import Union, Dict, Any, List
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model.dialog import (
    ElicitSlotDirective, DelegateDirective)
from ask_sdk_model import (
    Response, IntentRequest, DialogState, SlotConfirmationStatus, Slot)
from ask_sdk_model.slu.entityresolution import StatusCode

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Skill Builder object
sb = SkillBuilder()


@sb.request_handler(can_handle_func=is_request_type('LaunchRequest'))
def launch_request_handler(handler_input):
    """Handler for skill launch"""
    # type: (HandlerInput) -> Response
    logger.info(handler_input)
    speech = 'Welcome to LA Metro'

    return handler_input.response_builder.speak(speech).set_card(
        SimpleCard('Welcome', speech)).set_should_end_session(
        False).response


def check_mythical(handler_input):
    # type: (HandlerInput) -> bool
    is_mythical_creature = False
    resolved_value = get_resolved_value(
        handler_input.request_envelope.request, 'pet')
    if resolved_value is not None and resolved_value == 'mythical_creatures':
        is_mythical_creature = True
        handler_input.attributes_manager.session_attributes['mythical_creature']

    return is_mythical_creature


@sb.request_handler(can_handle_func=lambda input: not is_intent_name(
    'MythicalCreaturesIntent')(input) and check_mythical(input))
def mythical_creatures_intent(handler_input):
    logger.info('in mythical_creatures_intent')
    session_attr = handler_input.attributes_manager.session_attributes
    speech = random_phrase(slots_meta['pet']['invalid_responses']).format(
        session_attr['mythical_creature'])

    return handler_input.response_builder.speak(speech).response


@sb.request_handler(can_handle_func=lambda input: is_intent_name('PetMatchIntent')(input)
                    and input.request_envelope.request.dialog_state != DialogState.COMPLETED)
def in_progress_pet_match_intent(handler_input):
    # type: (HandlerInput) -> Response
    logger.info('in InProgressPetMatchIntent')
    current_intent = handler_input.request_envelope.request.intent
    prompt = ''

    for slot_name, current_slot in six.iteritems(current_intent.slots):
        if slot_name not in ['article', 'at_the', 'I want']:
            if current_slot.confirmation_status != SlotConfirmationStatus.CONFIRMED \
                    and current_slot.resolutions \
                    and current_slot.resolutions.resolutions_per_authority[0]:
                if current_slot.resolutions.resolutions_per_authority[0].status_code == StatusCode.ER_SUCCESS_MATCH:
                    if len(current_slot.resolutions.resolutions_per_authority[0].values) > 1:
                        prompt = 'Which would you like '

                        values = ' or '.join(
                            [e.value.name for e in current_slot.resolutions.resolutions_per_authority[0].values])
                        prompt += values + ' ?'
                        return handler_input.response_builder.speak(
                            prompt).ask(prompt).add_directive(
                                ElicitSlotDirective(
                                    slot_to_elicit=current_slot.name
                                )).response
                elif current_slot.resolutions.resolutions_per_authority[0].status_code == StatusCode.ER_SUCCESS_NO_MATCH:
                    if current_slot.name in required_slots:
                        prompt = f'What {current_slot.name} are you looking for?'
                        return handler_input.response_builder.speak(
                            prompt).ask(prompt).add_directive(
                                ElicitSlotDirective(
                                    slot_to_elicit=current_slot.name
                                )).response
    return handler_input.response_builder.add_directive(
        DelegateDirective(
            updated_intent=current_intent
        )).response


@sb.request_handler(can_handle_func=lambda input: is_intent_name('CompletedPetMatchIntent')(input)
                    and input.request_envelope.request.dialog_state == DialogState.COMPLETED)
def completed_pet_match_intent(handler_input):
    logger.info('in CompletedPetMatchIntent')
    filled_slots = handler_input.request_envelope.request.intent.slots
    slot_values = get_slot_values(filled_slots)
    pet_match_options = build_pet_match_options(
        host_name=pet_match_api['host_name'], path=pet_match_api['pets'],
        port=pet_match_api['port'], slot_values=slot_values)

    try:
        response = http_get(pet_match_options)
        if response['result']:
            speech = ("So a {} "
                      "{} "
                      "{} "
                      "energy dog sounds good for you. Consider a "
                      "{}".format(
                          slot_values["size"]["resolved"],
                          slot_values["temperament"]["resolved"],
                          slot_values["energy"]["resolved"],
                          response["result"][0]["breed"])
                      )
        else:
            speech = ("I am sorry I could not find a match for a "
                      "{} "
                      "{} "
                      "{} energy dog".format(
                          slot_values["size"]["resolved"],
                          slot_values["temperament"]["resolved"],
                          slot_values["energy"]["resolved"])
                      )
    except Exception as e:
        speech = ("I am really sorry. I am unable to access part of my "
                  "memory. Please try again later")
        logger.info("Intent: {}: message: {}".format(
            handler_input.request_envelope.request.intent.name, str(e)))

    return handler_input.response_builder.speak(speech).response


@sb.request_handler(can_handle_func=is_intent_name('AMAZON.HelpIntent'))
def help_intent_handler(handler_input):
    logger.info('in HelpIntentHandler')
    speech = 'This is pet match. I can help you find the perfect pet for you. You can say, I want a dog.'
    reprompt = 'What size and temperament are you looking for in a dog?'

    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input: is_intent_name('AMAZON.CancelIntent')(input)
                    or is_intent_name('AMAZON.StopIntent')(input))
def cancel_and_stop_intent_handler(handler_input):
    logger.info('in ExitIntentHandler')
    handler_input.response_builder.speak('Bye').set_should_end_session(True)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type('SessionEndedRequest'))
def session_ended_request_handler(handler_input):
    """Handler for skill session end."""
    # type: (HandlerInput) -> Response
    logger.info("In SessionEndedRequestHandler")
    logger.info("Session ended with reason: {}".format(
        handler_input.request_envelope.request.reason))
    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """Catch All Exception handler.

    This handler catches all kinds of exceptions and prints
    the stack trace on AWS Cloudwatch with the request envelope."""
    # Log the exception in CloudWatch Logs
    print('the exception: {}'.format(exception))
    logger.error(exception, exc_info=True)
    speech = "Sorry, I didn't get it. Can you please say it again!!"
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


@sb.global_response_interceptor()
def log_request(handler_input):
    """Response logger."""
    # type: (HandlerInput) -> None
    logger.info("Request Envelope: {}".format(
        handler_input.request_envelope))


@sb.global_response_interceptor()
def log_response(handler_input, response):
    """Response logger."""
    # type: (HandlerInput, Response) -> None
    logger.info("Response: {}".format(response))


# Data
required_slots = ["energy", "size", "temperament"]

slots_meta = {
    "pet": {
        "invalid_responses": [
            "I'm sorry, but I'm not qualified to match you with {}s.",
            "Ah yes, {}s are splendid creatures, but unfortunately owning one as a pet is outlawed.",
            "I'm sorry I can't match you with {}s."
        ]
    },
    "error_default": "I'm sorry I can't match you with {}s."
}

pet_match_api = {
    "host_name": "e4v7rdwl7l.execute-api.us-east-1.amazonaws.com",
    "pets": "/Test",
    "port": 443
}


# Utility functions
def get_resolved_value(request, slot_name):
    """Resolve the slot name from the request using resolutions."""
    # type: (IntentRequest, str) -> Union[str, None]
    try:
        return (request.intent.slots[slot_name].resolutions.
                resolutions_per_authority[0].values[0].value.name)
    except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
        logger.info("Couldn't resolve {} for request: {}".format(
            slot_name, request))
        logger.info(str(e))
        return None


def get_slot_values(filled_slots):
    """Return slot values with additional info."""
    # type: (Dict[str, Slot]) -> Dict[str, Any]
    slot_values = {}
    logger.info("Filled slots: {}".format(filled_slots))

    for key, slot_item in six.iteritems(filled_slots):
        name = slot_item.name
        try:
            status_code = slot_item.resolutions.resolutions_per_authority[0].status.code

            if status_code == StatusCode.ER_SUCCESS_MATCH:
                slot_values[name] = {
                    "synonym": slot_item.value,
                    "resolved": slot_item.resolutions.resolutions_per_authority[0].values[0].value.name,
                    "is_validated": True,
                }
            elif status_code == StatusCode.ER_SUCCESS_NO_MATCH:
                slot_values[name] = {
                    "synonym": slot_item.value,
                    "resolved": slot_item.value,
                    "is_validated": False,
                }
            else:
                pass
        except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
            logger.info(
                "Couldn't resolve status_code for slot item: {}".format(slot_item))
            logger.info(e)
            slot_values[name] = {
                "synonym": slot_item.value,
                "resolved": slot_item.value,
                "is_validated": False,
            }
    return slot_values


def random_phrase(str_list):
    """Return random element from list."""
    # type: List[str] -> str
    return random.choice(str_list)


def build_pet_match_options(host_name, path, port, slot_values):
    """Return options for HTTP Get call."""
    # type: (str, str, int, Dict[str, Any]) -> Dict
    path_params = {
        "SSET": "canine-{}-{}-{}".format(
            slot_values["energy"]["resolved"],
            slot_values["size"]["resolved"],
            slot_values["temperament"]["resolved"])
    }
    if host_name[:4] != "http":
        host_name = "https://{}".format(host_name)
    url = "{}:{}{}".format(host_name, str(port), path)
    return {
        "url": url,
        "path_params": path_params
    }


def http_get(http_options):
    url = http_options["url"]
    params = http_options["path_params"]
    response = requests.get(url=url, params=params)

    if response.status_code < 200 or response.status_code >= 300:
        response.raise_for_status()

    return response.json()


# ---------------------------------- Handlers ----------------------------------

# creating the lambda handler
lambda_handler = sb.lambda_handler()
