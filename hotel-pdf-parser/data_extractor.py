import json
import openai

from hotel_pdf_parser_constants import FIELD_NAMES

# needed locally
import os
from dotenv import load_dotenv
load_dotenv()


class DataExtractor:
    openai.api_key = os.getenv(key='OPENAI_API_KEY')
    SYSTEM_CONTENT = f"You are an assistant that helps extract data from text which is parsed from PDF invoices. " \
                     f"You will receive a text, and return a json with the following: " \
                     f"{{{FIELD_NAMES.VENUE_TITLE.inner}: <the full title of the vendor>, " \
                     f"{{{FIELD_NAMES.VENUE_ADDRESS.inner}: <the full address of the vendor>, " \
                     f"{{{FIELD_NAMES.VENDOR_PHONE.inner}: <the phone number of the vendor>, " \
                     f"{{{FIELD_NAMES.GUEST_FULL_NAME.inner}: <the full name of the customer>, " \
                     f"{FIELD_NAMES.GUEST_FIRST_NAME.inner}: <if the customer is an organization, this is the first name of the contact " \
                     f"for the customer. Otherwise, it is the first name of the customer>, " \
                     f"{FIELD_NAMES.GUEST_LAST_NAME.inner}: <if the customer is an organization, this is the last name of the contact " \
                     f"for the customer. Otherwise, it is the last name of the customer>, " \
                     f"{FIELD_NAMES.BILLING_ADDRESS.inner}: <the billing address of the customer>," \
                     f"{FIELD_NAMES.BILLING_CITY.inner}: <the billing city of the customer>," \
                     f"{FIELD_NAMES.BILLING_STATE.inner}: <the billing state of the customer>," \
                     f"{FIELD_NAMES.BILLING_ZIP.inner}: <the billing zip code of the customer>," \
                     f"{FIELD_NAMES.BILLING_COUNTRY.inner}: <the billing country of the customer>," \
                     f"{FIELD_NAMES.CHECK_IN_DATE.inner}: <date and time of the check in, in format dd:MM:yyyy HH:mm:ss>, " \
                     f"{FIELD_NAMES.CHECK_OUT_DATE.inner}: <date and time of the check out, in format dd:MM:yyyy HH:mm:ss>, "\
                     f"{FIELD_NAMES.ORDER_NUMBER.inner}: <Leave this blank>, "\
                     f"{FIELD_NAMES.TRANSACTION_AMOUNT.inner}: <Leave this blank>, " \
                     f"{FIELD_NAMES.RESERVATION_ID.inner}: <the reservation id or booking id. if this information is missing" \
                     f" leave this blank.>, " \
                     f"{FIELD_NAMES.COSTUMER_EMAIL.inner}: <the email address of the guest\customer.>, " \
                     f"{FIELD_NAMES.IS_CHECKED_IN.inner}: <if the costumer checked in return yes if not return no.>, " \
                     f"{FIELD_NAMES.IS_CONTACTLESS_CHECKED_IN.inner}: <if the costumer checked in via mobile or contactless return yes if the costumer checked in phisically return no.>, " \
                     f"{FIELD_NAMES.NUMBER_OF_GUESTS.inner}: <the total number of guests>, " \
                     f"{FIELD_NAMES.NUMBER_OF_NIGHTS.inner}: <the total number of nights>, " \
                     f"{FIELD_NAMES.ROOM_FEATURES.inner}: <the listing or room features>, " \
                     f"{FIELD_NAMES.CANCELLATION_DATE.inner}: <if the order was canceled, return the cancellation date>, " \
                     f"{FIELD_NAMES.TRANSACTION_METHOD.inner}: <the method by which the transaction was processed>, " \
                     f"{FIELD_NAMES.RETURNING_CUSTOMER.inner}: <an indication if the customer is a returning customer. Will be counted as a returning guest if they made more than 1 order using the same account>, " \
                     f"{FIELD_NAMES.BOOKING_CHANNEL.inner}: <the channel used by the cardholder to make the purchase/booking>, " \
                     f"{FIELD_NAMES.CREDITS_USED.inner}: <the amount of credits the customer used in this order>, " \
                     f"{FIELD_NAMES.CVM.inner}: <the Cardholder Verificaiton Method used (or not used) for the payment>}}.\n" \
                     f"For each value in the json, if you can not get the answer, return an empty string. " \
                     f"Your returned answer must always be a json as described"

    @staticmethod
    def extract_data(chunks):
        messages = [
            {"role": "system", "content": DataExtractor.SYSTEM_CONTENT},
            {"role": "user", "content": chunks[0]},  # TODO current path using chunk[0] only
        ]
        chatbot_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            response_format={"type": "json_object"},
            temperature=0,
            messages=messages,
        )
        output = chatbot_response.choices[0].message["content"]
        result = json.loads(output)
        return result
