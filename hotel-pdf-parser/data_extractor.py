import json
import openai

# needed locally
import os
from dotenv import load_dotenv
load_dotenv()


class DataExtractor:
    openai.api_key = os.getenv(key='OPENAI_API_KEY')
    SYSTEM_CONTENT = "You are an assistant that helps extract data from text which is parsed from PDF invoices." \
                     "You will receive a text, and return a json with the following: {customer_full_name: <the full name of the customer>" \
                     ", contact_first_name: <if the customer is an organization, this is the first name of the contact for the customer. " \
                     "Otherwise, it is the first name of the customer>, contact_last_name: <if the customer is an organization, this is " \
                     "the last name of the contact for the customer. Otherwise, it is the last name of the customer>, check_in: <date of " \
                     "check in>, check_out: <date of check out>}.\n" \
                     "For each value in the json, if you can not get the answer, return 'NaN'. Your returned answer must always be a json " \
                     "as described"

    @staticmethod
    def extract_data(chunks):
        messages = [
            {"role": "system", "content": DataExtractor.SYSTEM_CONTENT},
            {"role": "user", "content": chunks[0]},  # TODO current path using chunk[0] only
        ]
        chatbot_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        output = chatbot_response.choices[0].message["content"]
        result = json.loads(output)
        return result
