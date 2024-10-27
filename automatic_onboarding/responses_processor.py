from typing import Union, List, Dict
from constants import OUTPUTS
import openai
import os


def get_response_gpt(prompt):
    # openai.api_key = st.secrets["openai"]["api_key"]
    openai.api_key = os.getenv(key='OPENAI_API_KEY')
    messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]
    chatbot_response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # "gpt-3.5-turbo-16k",
        temperature=0,
        messages=messages,
    )
    output = chatbot_response.choices[0].message["content"]
    return output


class ResponsesProcessor:

    @staticmethod
    def process_llm_responses(responses: List[Dict]) -> Dict[str, Union[str, List[str]]]:
        """
        Notice that the first dictionary comes from the general questions, and the others from the advanced.
        :param responses:
        :return:
        """
        # take the first dictionary which is relevant for the general
        result = responses.pop(0)

        # change the company field name to merchant_name
        result[OUTPUTS.MERCHANT_NAME] = result.pop(OUTPUTS.COMPANY)

        # iterate over each key which has a value that is a list. We shall take their union.
        for list_field in OUTPUTS.LIST_LIKE_OUTPUTS:
            if list_field in result:
                # was part of the general
                continue
            lst = [dic.get(list_field, []) for dic in responses]
            flatten_lst = [item for sublist in lst for item in sublist]
            result[list_field] = sorted(list(set(flatten_lst)))

        # process the customer support email. If their are several, ask openai which is the most appropriate
        optional_mails = [dic.get(OUTPUTS.CUSTOMER_SUPPORT_EMAIL) for dic in responses]
        optional_mails = list(set([m for m in optional_mails if m is not None and m not in ('', 'NULL', 'None')]))
        if len(optional_mails) == 0:
            result[OUTPUTS.CUSTOMER_SUPPORT_EMAIL] = None
        elif len(optional_mails) == 1:
            result[OUTPUTS.CUSTOMER_SUPPORT_EMAIL] = optional_mails[0]
        else:
            optional_mails_str = str(optional_mails).replace("'", "")
            prompt = f"See this list of emails: {optional_mails_str}. Which of them is the most probable to be the customer support " \
                     f"email for the company called {result[OUTPUTS.MERCHANT_NAME]}? " \
                     f"return the answer without any explanations or added characters."
            result[OUTPUTS.CUSTOMER_SUPPORT_EMAIL] = get_response_gpt(prompt)

        return result
