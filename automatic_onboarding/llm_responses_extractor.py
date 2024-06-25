import concurrent.futures
# from google.cloud import aiplatform
# from vertexai.preview.language_models import TextGenerationModel
# from google.oauth2 import service_account
import streamlit as st
from apify_client import ApifyClient
from typing import Union, List, Dict
import ast
import openai

from constants import QuestionnairePrompts
from responses_processor import ResponsesProcessor

# needed locally
import os
from dotenv import load_dotenv
load_dotenv()

class LlmResponsesExtractor:

    def __init__(self):
        pass

    # @staticmethod
    # def get_response_vertax(prompt):
    #
    #     # Create API client.
    #     credentials = service_account.Credentials.from_service_account_info(
    #         st.secrets["connections"]
    #     )
    #     aiplatform.init(credentials=credentials)
    #     aiplatform.init(project='datascience-393713')
    #
    #     model = TextGenerationModel.from_pretrained("text-bison@001")
    #     response = model.predict(
    #         prompt,
    #         temperature=0.3,
    #         max_output_tokens=1024,
    #     )
    #     return response.text

    @staticmethod
    def get_response_gpt(prompt):
        # openai.api_key = st.secrets["openai"]["api_key"]
        openai.api_key = os.getenv(key='OPENAI_API_KEY')
        messages = [
            {"role": "system", "content": "You are an assistant that helps to choose the best options based on a company description."},
            {"role": "user", "content": prompt},
        ]
        chatbot_response = openai.ChatCompletion.create(
            model="gpt-4o",  # "gpt-3.5-turbo-16k",
            temperature=0,
            response_format={"type": "json_object"},
            messages=messages,
        )
        output = chatbot_response.choices[0].message["content"]
        return output

    # @staticmethod
    # def get_response_single_prompt(prompt):
    #     return LlmResponsesExtractor.get_response_vertax(prompt)

    @staticmethod
    def process_question_apify(question):
        # Initialize the ApifyClient with your API token
        # client = ApifyClient(st.secrets["apify"]["api_key"])
        apify_api_token = os.getenv(key="APIFY_API_TOKEN")
        client = ApifyClient(apify_api_token)
        urls = question["urls"]
        prompt = question["prompt"]

        # Prepare the Actor input
        run_input = {
            "startUrls": urls,
            # "globs": [],
            "linkSelector": "a[href]",  # a[href*=terms],a[href*=refund]",
            "instructions": prompt,
            "maxCrawlingDepth": 1,
            "model": "gpt-4o",  # "gpt-3.5-turbo-16k",
            "openaiApiKey": os.getenv(key='OPENAI_API_KEY'),  # st.secrets["openai"]["api_key"],
            # "targetSelector": "",
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
    def get_questionnaire_responses(url: str, urls: List[str] = None) -> List[Dict]:
        llm_prompts = [{"prompt": QuestionnairePrompts.DESCRIPTION, "urls": [{"url": url}]},
                       {"prompt": QuestionnairePrompts.CHANNELS_BILLINGS_DELIVERY_EMAIL, "urls": urls},
                       {"prompt": QuestionnairePrompts.POLICIES, "urls": urls},
                       {"prompt": QuestionnairePrompts.LIABILITY, "urls": urls}]

        # Using ThreadPoolExecutor to parallelize the processing of questions
        with concurrent.futures.ThreadPoolExecutor() as executor:
            responses_gpt = list(executor.map(LlmResponsesExtractor.process_question_apify, llm_prompts))

        print("###########")
        print(responses_gpt)
        print("###########")

        if len(responses_gpt) > 0 and len(responses_gpt[0]) > 0 and responses_gpt[0][0] is not None:
            merchant_description = responses_gpt[0][0]["long_description"]
            industry_prompt = merchant_description + " " + QuestionnairePrompts.INDUSTRY
            offerings_prompt = merchant_description + " " + QuestionnairePrompts.OFFERINGS
            responses_gpt = responses_gpt + [ast.literal_eval(LlmResponsesExtractor.get_response_gpt(industry_prompt))]
            responses_gpt = responses_gpt + [ast.literal_eval(LlmResponsesExtractor.get_response_gpt(offerings_prompt))]

        print("Full responses: ", responses_gpt)
        # responses = responses_gpt
        processed_responses_gpt = ResponsesProcessor.process_llm_responses(responses_gpt)
        print("------------------------------------------------------------------------------------------------------")
        print("Processed responses: ", processed_responses_gpt)
        responses = processed_responses_gpt

        return responses

