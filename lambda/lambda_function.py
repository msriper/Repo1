# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import csv
import requests
import io
import calendar
import pandas

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hello! Welcome. Would you like to know your zodiac sign? Or perhaps would be interested in recommendations for a book?"
        reprompt_text = "Interested in your zodiac sign? I was born Nov. 6th, 2014. When were you born? Or Perhaps, interested in book recommendations for any genre or published year?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )


class CaptureZodiacSignIntentHandler(AbstractRequestHandler):
    """Handler for Capture ZodiacSign Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CaptureZodiacSignIntent")(handler_input)

    def filter(self, X):
        date = X.split()
        month = date[0]
        month_as_index = list(calendar.month_abbr).index(month[:3].title())
        day = int(date[1])
        return (month_as_index,day)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots
        year = slots["year"].value
        month = slots["month"].value
        day = slots["day"].value
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTiZaKFAoeorm1c0YTfTs5BaXAkGdKVX14PCuQGrL4rDHFwfs4Z5nnTEdYF56QMkw/pub?gid=1561241654&single=true&output=csv"
        response = requests.get(url)
        csv_content = response.content
        row = csv_content.decode('utf-8').splitlines()
        rows = row[1:] # excluding the first row

        zodiac = ''
        month_as_index = list(calendar.month_abbr).index(month[:3].title())
        usr_dob = (month_as_index,int(day))
        for sign in rows:
            start, end , zodiac = sign.split(',')
            if self.filter(start) <= usr_dob <= self.filter(end):
                zodiac = zodiac
                break

        speak_output = 'I see you were born on the {day} of {month} {year}, which means that your zodiac sign will be {zodiac}.'.format(month=month, day=day, year=year, zodiac=zodiac)


        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .ask("Would you like zodiac sign of another?")
                .response
        )

class RecommendBookIntentHandler(AbstractRequestHandler):
    """Handler for RecommendBookIntent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("RecommendBookIntent")(handler_input)
    
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots
        
        genre = slots["genre"].value if slots["genre"] and slots["genre"].value else None
        published_year = slots["published_year"].value if slots["published_year"] and slots["published_year"].value else None
        author = slots["author_name"].value if slots["author_name"] and slots["author_name"].value else None

        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQIwlsnpGztoV-nSMpCjiZpLhX_Hgdumu457_NPZpXXdMxDUbikrmJwERPN9MCMEA/pub?gid=1336688026&single=true&output=csv"
        response = requests.get(url)
        csv_data = response.text
        df = pandas.read_csv(io.StringIO(csv_data))
        df['Year'] = df['Year'].astype(str)
        books_df = None
        books_end = None
        if genre and published_year and author:
            books_df = df[(df['Genre'].str.lower() == genre.lower()) &
                      (df['Year'].str == published_year) &
                      (df['Author'].str.lower() == author.lower())][['Title', 'Author']]
        elif genre and published_year:
            books_df = df[(df['Genre'].str.lower() == genre.lower()) &
                      (df['Year'] == published_year)][['Title', 'Author']]
        elif published_year and author:
            books_df = df[(df['Year'] == published_year) &
                      (df['Author'].str.lower() == author.lower())][['Title', 'Author']]
        elif author and genre:
            books_df = df[(df['Genre'].str.lower() == genre.lower()) &
                      (df['Author'].str.lower() == author.lower())][['Title', 'Author']]
        elif genre:
            books_df = df[df['Genre'].str.lower() == genre.lower()][['Title', 'Author']]
        elif published_year:
            books_df = df[df['Year'] == published_year][['Title', 'Author']]
        elif author:
            books_df = df[df['Author'].str.lower() == author.lower()][['Title', 'Author']]
        else:
            books_df = df[['Title', 'Author']].head(2)
            books_end = ' Would you like another recommendation? Why not provide a genre or author name or perhaps a published year you are interested in?'
        
        parts = []
        if published_year:
            parts.append('PUBLISHED YEAR: ' + str(published_year))
        if author:
            parts.append('AUTHOR: ' + author)
        if genre:
            parts.append('GENRE: '+ genre)
        
        context = ' '.join(parts)
        
        if books_df is None or books_df.empty:
            books = "I couldn't find any book matches based on your preferences."
        else:
            books = '\n'.join([f"TITLE: {row['Title']} by AUTHOR: {row['Author']}; " for _, row in books_df.iterrows()])

        if books_end:
            books += books_end
        
        speak_output = 'Here are your book recommendation(s) for {} ===>> {}.'.format(context, books)
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                #.ask("add a reprompt if you want to keep the session open for the user to respond")
                .ask("Would you like another recommendation?")
                .response
        )



class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say ask for zodiac sign, a book recommendation or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CaptureZodiacSignIntentHandler())
sb.add_request_handler(RecommendBookIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()