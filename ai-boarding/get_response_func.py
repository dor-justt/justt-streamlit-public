import dotenv
import concurrent.futures
from google.cloud import aiplatform
from vertexai.preview.language_models import TextGenerationModel
import ast
from google.oauth2 import service_account
import streamlit as st
import logging
import os
import openai
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.llms import OpenAI, OpenAIChat
from apify_client import ApifyClient
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from typing import Union, List, Dict
import pandas as pd

os.environ["SERPAPI_API_KEY"] = st.secrets["google"]["api_key"]
openai.api_key = st.secrets["openai"]["api_key"]


def get_links(website_link: str) -> List:
    """
    get all sub-URLs in a given URL with maximum depth of 1
    :param website_link: parent URL
    :return: a list of URLs
    """
    # create empty dict to not repeat the same link
    dict_href_links = {}

    # get html data
    html_data = requests.get(website_link).text #getdata(website_link)
    soup = BeautifulSoup(html_data, "html.parser")
    list_links = []
    for link in soup.find_all("a", href=True):

        # Append to list if new link contains original link
        if str(link["href"]).startswith((str(website_link))):
            list_links.append(link["href"])

        # Include all href that do not start with website link but with "/"
        if str(link["href"]).startswith("/"):
            if link["href"] not in dict_href_links:
                dict_href_links[link["href"]] = None
                link_with_www = website_link + link["href"][1:]
                list_links.append(link_with_www)

    # remove duplicates
    list_links = list(set(list_links))
    return list_links

def process_question_vertax(question):
    # trim prompt since there is a maximum input limit of ~8000 tokens
    # trimmed_question = ' '.join(question.split()[:6000])
    model = TextGenerationModel.from_pretrained("text-bison@001")
    response = model.predict(
        question,
        temperature=0.3,
        max_output_tokens=1024,
    )
    response.text
    return response.text

def process_question_gpt_using_search(question: str) -> str:
    """
    get response using chat GPT using search tool
    :param question: question prompt
    :return: chat GPT response
    """
    llm = OpenAIChat(temperature=0, model="gpt-3.5-turbo-16k")
    tools = load_tools(["serpapi"], llm=llm)
    agent = initialize_agent(tools, llm,
                             agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                             verbose=True,
                             handle_parsing_errors=True)
    openai.api_key = st.secrets["openai"]["api_key"]
    try:
        output = agent.run(question)
    except:
        output = None
    try:
        formatted_response = ast.literal_eval(output.strip().strip('`').replace("json", "").replace("\n", ""))
    except:
        formatted_response = None
    return formatted_response

def aggregate_responses(responses: Union[List[Dict], List[str]], response_type: str) -> Union[Dict,str, List[str]]:
    if len(responses) == 1:
        best_response = responses[0]
    elif len(responses) == 0:
        best_response = "Information not found"
    else:
        if response_type == "list":
            total_channels_responses = len(responses)
            merged_channels_responses = pd.Series(sum(responses, []))
            channels_freq = merged_channels_responses.value_counts() / total_channels_responses
            best_response = channels_freq[channels_freq >= 0.5].index.to_list()
        elif response_type == "json":
            summary_length = [len(response["summary"]) for response in responses]
            longest_summary_index = summary_length.index(max(summary_length))
            best_response = responses[longest_summary_index]
        elif response_type == "str":
            response_length = [len(response) for response in responses]
            longest_summary_index = response_length.index(max(response_length))
            best_response = responses[longest_summary_index]
    return best_response


def choose_best_response(responses: List[List[Dict]]):
    best_responses = dict()

    # company name, description, industry
    best_responses["merchant_name"] = responses[0][0]["company"]
    best_responses["description"] = responses[0][0]["description"]
    best_responses["industry"] = responses[0][0]["industry"]

    # channels, billing, email
    channels_responses = [response["channels"] for response in responses[1] if response is not None and len(response["channels"])>0 and
                          response["channels"] != "NULL" and isinstance(response["channels"], list) and response["channels"] is not None]
    best_responses["channels"] = aggregate_responses(responses=channels_responses, response_type="list")

    billings_responses = [response["billings"] for response in responses[1] if response is not None and len(response["billings"]) > 0 and
                          response["billings"] != "NULL" and isinstance(response["billings"], list) and response[
                              "billings"] is not None]
    best_responses["billings"] = aggregate_responses(responses=billings_responses, response_type="list")

    # choose the most common email address
    email_responses = [response["emailAddress"] for response in responses[1] if response is not None and "@" in response["emailAddress"]]
    if len(email_responses) == 0:
        best_responses["emailAddress"] = "Information not found"
    else:
        best_responses["emailAddress"] = pd.Series(email_responses).value_counts().index[0]

    # customer_support, cancellation, refund_policy
    customer_support_responses = [response["customer_support"] for response in responses[2] if response is not None and
                                  "customer_support" in response.keys() and
                                  response["customer_support"] != "NULL" and
                                  "NULL" not in response["customer_support"] and
                                  isinstance(response["customer_support"], Dict) and
                                  response["customer_support"] is not None]
    best_responses["customer_support"] = aggregate_responses(responses=customer_support_responses, response_type="json")

    cancellation_responses = [response["cancellation"] for response in responses[2] if response is not None and
                              "cancellation" in response.keys() and
                                  response["cancellation"] != "NULL" and
                                  "NULL" not in response["cancellation"] and
                                  isinstance(response["cancellation"], Dict) and
                                  response["cancellation"] is not None]
    best_responses["cancellation"] = aggregate_responses(responses=cancellation_responses, response_type="json")

    refund_policy_responses = [response["refund_policy"] for response in responses[2] if response is not None and
                               "refund_policy" in response.keys() and
                              response["refund_policy"] != "NULL" and
                              "NULL" not in response["refund_policy"] and
                              isinstance(response["refund_policy"], str) and
                              response["refund_policy"] is not None]
    best_responses["refund_policy"] = aggregate_responses(responses=refund_policy_responses, response_type="str")

    delivery_methods_responses = [response["delivery_methods"] for response in responses[3] if response is not None and
                                  "delivery_methods" in response.keys() and
                          len(response["delivery_methods"]) > 0 and
                          response["delivery_methods"] != "NULL" and isinstance(response["delivery_methods"], list) and response[
                              "delivery_methods"] is not None]
    best_responses["delivery_methods"] = aggregate_responses(responses=delivery_methods_responses, response_type="list")

    liability_responses = [response["liability"] for response in responses[3] if response is not None and
                                  "liability" in response.keys() and
                                  "NULL" not in response["liability"] and
                           "X" not in response["liability"] and
                                  response["liability"] != "NULL" and isinstance(response["liability"],
                                                                                        Dict) and response[
                                      "liability"] is not None]
    if len(liability_responses) == 0:
        best_responses["liability"] = "Information not found"
    else:
        best_responses["liability"] = pd.Series(liability_responses)[0]

    return best_responses



def process_question_apify(question):
    # Initialize the ApifyClient with your API token
    client = ApifyClient(st.secrets["apify"]["api_key"])
    urls = question["urls"]
    prompt = question["prompt"]

    # Prepare the Actor input
    run_input = {
        "startUrls": urls,
        "globs": [],
        "linkSelector": "a[href]", #a[href*=terms],a[href*=refund]",
        "instructions": prompt,
        "maxCrawlingDepth": 1,
        "model": "gpt-3.5-turbo-16k",
        "openaiApiKey": st.secrets["openai"]["api_key"],
        "targetSelector": "",
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
    for item in client.dataset(run["defaultDatasetId"]).iterate_items(): #.iterate_items(limit=1):
        output = item["answer"]
        try:
            formatted_response =  ast.literal_eval(output.strip("'").strip().strip('`').replace("json", "").replace("\n", ""))
        except:
            formatted_response = None
        formatted_responses.append(formatted_response)

    return formatted_responses


def get_response_single_prompt(prompt):

    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["connections"]
    )
    aiplatform.init(credentials=credentials)
    aiplatform.init(project='datascience-393713')
    print("------prompt: ", prompt)
    return process_question_vertax(prompt)

def get_questionnaire_responses(url: str) -> [Dict, List[Dict]]:

    # Create API client.
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["connections"]
    )
    aiplatform.init(credentials=credentials)
    aiplatform.init(project='datascience-393713')

    get_name_description_industry = f"From the information in this website, answer the following three questions and return the " \
                                    "answers in a json format: {'company': answer_to_question_1, " \
                                    "'description': answer_to_question_2, 'industry': answer_to_question_3}. " \
                                    "1. Search the company name. Return the answer as a string. " \
                                    "2. Describe the company in up to five sentences, and no less than " \
                                    f"three sentences. Focus on what they do as a company, and what services they offer. " \
                                    f"Be neutral and descriptive. Return the answer as a string " \
                                    f"3. See this list of one-word industry descriptions: " \
                                    f"'Retail, Financial Services, Travel, Gaming, Crypto, Software Subscription, Gambling, " \
                                    f"Ticketing, Delivery'. Choose the description that suits the provided company the most. You can " \
                                    f"only use the options provided above, don't invent other options. Return the answer as a string."
    get_channels_billing_email = f"From the information in this website, answer the following three questions and return the " \
                                 "answers in a json format: {'channels': answer_to_question_1, " \
                                 "'billings': answer_to_question_2, 'emailAddress': answer_to_question_3}. " \
                                 "1. See this list of selling channel options: " \
                                 f"'Website, Mobile app, 3rd party, Phone calls'. Choose only the options the provided " \
                                 f"company uses to sell their products. You can only choose out the options provided above, " \
                                 f"don't invent other options. Return the answer as a list of strings" \
                                 f"2. See this list of billing models: 'One time payment, " \
                                 f"Subscriptions, Installments'. out of this list, Choose only the options the provided company " \
                                 f"offers. You can only choose out the options provided above, don't show other options. Choose as " \
                                 f"many answers as applicable, but not options that are not listed. Return the answer as a list of strings. " \
                                 f"3. What is the merchant's customer support email? Return the answer as a string."
    get_terms_info = f"From the information in this website, answer the following three questions and return the " \
                     "answers in a json format: {'customer_support': answer_to_question_1, " \
                     "'cancellation': answer_to_question_2, 'refund_policy': answer_to_question_3}. " \
                     "If the text from the website does not contain required information to answer the question replace " \
                     "X with 'NULL'. Don't answer based on your previous knowledge." \
                     "1. What is the maximal timeframe mentioned " \
                     "per purchase for customer support? Summarize it and also provide the relevant paragraph " \
                     "from the Terms of Service and save it as quote. If there are any specific conditions for " \
                     "it, mention them. Provide URL for the source you use for your answer. Return the answer " \
                     "as a json in this format: {'timeframe': X, 'summary': X, 'quote': X , 'specificConditions': X, 'source': X} " \
                     "2. What is the maximal timeframe mentioned per purchase for the cancellation policy? Summarize " \
                     "it and also provide the relevant quotes from the website. If there are any specific " \
                     "conditions for it, mention them. Provide URL for the source you use for your answer. " \
                     "Return the answer as a json in this format: {'timeframe': X, 'summary': X, 'quote': X , " \
                     "'specificConditions': X, 'source': X}" \
                     "3. Based on the information on the website, summarize the exact conditions to get a refund. return it as a string"
    get_crypto_info = f"From the information in this website answer the following question. Does the platform use " \
                      "blockchain to transfer the crypto or the crypto transfer is done on it’s own platform? if the " \
                      "merchant's industry is not crypto return NULL. " \
                      "Return the answer as a json in this format: {'crypto_transfers': blockchain\internal system}"
    get_delivery_and_liability = f"From the information in this website, answer the following two questions and return the " \
                           "answers in a json format: {'delivery_methods': answer_to_question_1, " \
                           "'liability': answer_to_question_2}. " \
                           "1. what delivery methods does the seller offer? Shipping, in store pickup or other? " \
                                 "If the merchant doesn't sell products return NULL. Return " \
                           "the answer as a list of strings." \
                           "2. who takes liability on the following topics? Chargebacks (fraud transactions and " \
                           "service), delivery issues and product quality? Return the answer as a json in this format: " \
                           "{'Chargebacks': X, 'delivery_issues': X, 'quality': X}. If this information is missing, replace X with NULL."

    # scrape start URLs for apify tool
    links = get_links(url)
    urls = [{"url": url}]
    if len(links) > 0:
        word_list = ["terms", "refund", "cancel", "info", "about", "faq", "policy", "policies"]

        # Function to check if a string contains any word from the word list
        def contains_word(string, word_list):
            return any(word in string for word in word_list)

        # Filter strings that contain at least one word from the word list and add the parent link
        urls = urls + [{"url": string} for string in links if contains_word(string, word_list) and ".pdf" not in string]

    questions_gpt = [{"prompt": get_name_description_industry, "urls": [{"url": url}]},
                     {"prompt": get_channels_billing_email, "urls": urls},
                     {"prompt": get_terms_info, "urls": urls},
                     {"prompt": get_delivery_and_liability, "urls": urls}]
                     # {"prompt": get_crypto_info, "urls": urls}]

    # Using ThreadPoolExecutor to parallelize the processing of questions
    with concurrent.futures.ThreadPoolExecutor() as executor:
        responses_gpt = list(executor.map(process_question_apify, questions_gpt))

    # responses_gpt = []
    # for question in questions_gpt:
    #     responses_gpt.append(process_question_apify(question))

    print("Full responses_gpt: ", responses_gpt)
    responses_gpt = choose_best_response(responses_gpt)
    print("Best responses_gpt: ", responses_gpt)
    responses = responses_gpt
    questions = questions_gpt

    return responses, questions

