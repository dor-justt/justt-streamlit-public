from typing import Union, List, Dict
import pandas as pd

import constants
from constants import  ResponseCategories


class ResponsesProcessor:

    @staticmethod
    def aggregate_responses(responses: Union[List[Dict], List[str]],
                            response_type: str) -> Union[Dict, str, List[str]]:
        if len(responses) == 1:
            best_response = responses[0]
        elif len(responses) == 0:
            best_response = "Information not found"
        else:
            if response_type == "list":
                # choose most common options
                total_channels_responses = len(responses)
                merged_channels_responses = pd.Series(sum(responses, []))
                channels_freq = merged_channels_responses.value_counts() / total_channels_responses
                best_response = channels_freq[channels_freq >= 0.5].index.to_list()
            elif response_type == "json":
                # choose the longest response
                summary_length = [len(response["summary"]) for response in responses]
                longest_summary_index = summary_length.index(max(summary_length))
                best_response = responses[longest_summary_index]
                if "Merchant doesn't sell physical goods" in best_response:
                    best_response = "Merchant doesn't sell physical goods"
            elif response_type == "str":
                # choose the longest response
                response_length = [len(response) for response in responses]
                longest_summary_index = response_length.index(max(response_length))
                best_response = responses[longest_summary_index]
        return best_response

    @staticmethod
    def clean_categories(categories_response: List[str], categories_to_keep: List[str]):
        return [cat for cat in categories_response if cat.lower() in categories_to_keep]

    @staticmethod
    def process_llm_responses(responses: List[List[Dict]]):

        best_responses = dict()

        # company name, description, industry, offerings
        best_responses["merchant_name"] = responses[0][0]["company"]
        best_responses["description"] = responses[0][0]["description"]
        best_responses["industry"] = responses[4]["industry"] if len(responses)>4 else None
        best_responses["offerings"] = responses[5]["offerings"] if len(responses)>4 else None

        print("---- offerings: ", best_responses["offerings"])
        print("---- offerings type: ", type(best_responses["offerings"]))

        # # clean_categories
        # best_responses["industry"] = ResponsesProcessor.clean_categories(categories_response=best_responses["industry"],
        #                                               categories_to_keep=ResponseCategories().INDUSTRY)
        # best_responses["offerings"] = ResponsesProcessor.clean_categories(categories_response=best_responses["offerings"],
        #                  categories_to_keep=ResponseCategories().OFFERINGS)

        # channels - choose the most common options
        channels_responses = [response["channels"] for response in responses[1] if response is not None and
                              "channels" in response.keys() and
                              response["channels"] is not None and
                              response["channels"] != "NULL" and
                              len(response["channels"]) > 0 and
                              isinstance(response["channels"], list)]
        best_responses["channels"] = ResponsesProcessor.aggregate_responses(responses=channels_responses, response_type="list")

        # billings - choose the most common options
        billings_responses = [response["billings"] for response in responses[1] if response is not None and
                              "billings" in response.keys() and
                              response["billings"] is not None and
                              response["billings"] != "NULL" and
                              len(response["billings"]) > 0 and
                              isinstance(response["billings"], list)]
        best_responses["billings"] = ResponsesProcessor.aggregate_responses(responses=billings_responses, response_type="list")

        # delivery - choose the most common options
        delivery_methods_responses = [response["delivery_methods"] for response in responses[1] if response is not None and
                                      "delivery_methods" in response.keys() and
                                      response["delivery_methods"] != "NULL" and
                                      isinstance(response["delivery_methods"], list) and
                                      response["delivery_methods"] is not None and
                                      len(response["delivery_methods"]) > 0]
        best_responses["delivery_methods"] = ResponsesProcessor.aggregate_responses(responses=delivery_methods_responses, response_type="list")
        if "Merchant doesn't sell physical goods" in best_responses["delivery_methods"] or "Physical Goods" not in best_responses["offerings"]:
            best_responses["delivery_methods"] = "Merchant doesn't sell physical goods"

        # Email address - choose the most common
        email_responses = [response["emailAddress"] for response in responses[1] if
                           response is not None and "@" in response["emailAddress"]]
        if len(email_responses) == 0:
            best_responses["emailAddress"] = "Information not found"
        else:
            # present all emails that contain the word support
            support_emails = [email for email in pd.Series(email_responses).unique() if "support" in email]
            if len(support_emails)>0:
                best_responses["emailAddress"] = support_emails
            else:
                # present all emails
                best_responses["emailAddress"] = pd.Series(email_responses).unique()

        # cancellation
        cancellation_responses = [response["cancellation"] for response in responses[2] if response is not None and
                                  "cancellation" in response.keys() and
                                  response["cancellation"] != "NULL" and
                                  "NULL" not in response["cancellation"] and
                                  isinstance(response["cancellation"], Dict) and
                                  response["cancellation"] is not None]
        best_responses["cancellation"] = ResponsesProcessor.aggregate_responses(responses=cancellation_responses, response_type="json")

        # refund policy
        refund_policy_responses = [response["refund_policy"] for response in responses[2] if response is not None and
                                   "refund_policy" in response.keys() and
                                   response["refund_policy"] != "NULL" and
                                   "NULL" not in response["refund_policy"] and
                                   isinstance(response["refund_policy"], str) and
                                   response["refund_policy"] is not None]
        best_responses["refund_policy"] = ResponsesProcessor.aggregate_responses(responses=refund_policy_responses, response_type="str")

        # return policy
        return_policy_responses = [response["return_policy"] for response in responses[2] if response is not None and
                                   "return_policy" in response.keys() and
                                   response["return_policy"] != "NULL" and
                                   "NULL" not in response["return_policy"] and
                                   isinstance(response["return_policy"], str) and
                                   response["return_policy"] is not None]
        best_responses["return_policy"] = ResponsesProcessor.aggregate_responses(responses=return_policy_responses, response_type="str")

        # liability
        liability_responses = [response["liability"] for response in responses[3] if response is not None and
                               "liability" in response.keys() and
                               "NULL" not in response["liability"] and
                               "X" not in response["liability"] and
                               response["liability"] != "NULL" and
                               isinstance(response["liability"], Dict)
                               and response["liability"] is not None]
        if len(liability_responses) == 0:
            best_responses["liability"] = "Information not found"
        else:
            liability_responses
            best_responses["liability"] = pd.Series(liability_responses)[0]

        return best_responses
