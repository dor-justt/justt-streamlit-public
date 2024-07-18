import concurrent.futures

import streamlit as st
from apify_client import ApifyClient
from typing import List, Dict, Union
import ast

from constants import QuestionnairePrompts, OPENAI_MODEL
from responses_processor import ResponsesProcessor

# needed locally
import os
from dotenv import load_dotenv
load_dotenv()


class LlmResponsesExtractor:

    @staticmethod
    def process_question_apify(question):
        # Initialize the ApifyClient with your API token
        # apify_api_token = st.secrets["apify"]["api_key"]
        apify_api_token = os.getenv(key="APIFY_API_TOKEN")
        client = ApifyClient(apify_api_token)
        urls = question["urls"]
        prompt = question["prompt"]

        # Prepare the Actor input
        run_input = {
            "startUrls": urls,
            "linkSelector": "a[href]",
            "instructions": prompt,
            "maxCrawlingDepth": 1,
            "model": OPENAI_MODEL,
            "openaiApiKey": os.getenv(key='OPENAI_API_KEY'),  # st.secrets["openai"]["api_key"],
            "schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Page title",
                    },
                    "description": {
                        "type": "string",
                        "description": "Page description",
                    },
                },
                "required": [
                    "title",
                    "description",
                ],
            },
            "proxyConfiguration": {"useApifyProxy": True},
        }
        # Run the Actor and wait for it to finish
        run = client.actor("drobnikj/extended-gpt-scraper").call(run_input=run_input)

        # Fetch and print Actor results from the run's dataset (if there are any)
        formatted_responses = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            output = item["answer"]
            try:
                formatted_response = ast.literal_eval(output.strip("'").strip().strip('`').replace("json", "").replace("\n", ""))
            except:
                formatted_response = None
            formatted_responses.append(formatted_response)

        return formatted_responses

    @staticmethod
    def get_questionnaire_responses(url: str, urls: List[Dict[str, str]] = None) -> Dict[str, Union[str, List[str]]]:
        """
        Uses openai through apify in order to answer the questionare with the url that was given, and the list of child urls
        :param url: the 'parent' url that was given from the user.
        :param urls: The list of child urls in the shape of [{"url": url1}, {"url": url2}, ...]
        :return: Dictionary with the questionare answers
        """
        llm_prompts = [{"prompt": QuestionnairePrompts.GENERAL, "urls": [{"url": url}]},
                       {"prompt": QuestionnairePrompts.ADVANCED, "urls": urls}]

        # use multithread to speed up performance
        with concurrent.futures.ThreadPoolExecutor() as executor:
            responses_gpt_raw: List[List[Dict]] = list(executor.map(LlmResponsesExtractor.process_question_apify, llm_prompts))

        # We got a list of lists. One list per prompt. Each such list is of size #urls. unpack the list of lists to a single list
        responses_gpt = [item for sublist in responses_gpt_raw for item in sublist if item is not None]

        print("###########")
        print("###########")
        print('response length: ', len(responses_gpt))
        for response in responses_gpt:
            print(response)
            print('**************')
        print("###########")
        print("###########")

        print("Full responses: ", responses_gpt)
        # aggregate and process the results
        processed_responses_gpt = ResponsesProcessor.process_llm_responses(responses_gpt)
        print("------------------------------------------------------------------------------------------------------")
        print("Processed responses: ", processed_responses_gpt)
        responses = processed_responses_gpt

        return responses
