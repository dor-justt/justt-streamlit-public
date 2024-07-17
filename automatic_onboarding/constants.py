from dataclasses import dataclass, field
from typing import List


REDUCE_HELLUCINATIONS_STR: str = "You can only choose out the options provided above, " \
                                 "dont invent other options. Return the answer as a list of strings, which can be empty if none of the " \
                                 "options apply. Include on ly answers you are certain of."


class OUTPUTS:
    COMPANY = 'company'
    DESCRIPTION = 'description'
    INDUSTRY = 'industry'
    BUSINESS_OPERATION = 'business operation'
    SELLS_THROUGH = 'sells through'
    GEOGRAPHICAL_AREAS = 'geographical areas'
    WHEN_CUSTOMER_MAKES_A_PAYMENT = 'when a customer makes a payment'
    DIRECT_SALES_CHANNELS = 'direct sales channels'
    BILLING_MODELS = 'billing models'
    TERMS_COVERAGE = 'terms coverage'
    INSURANCE_OPTIONS = 'insurance options'
    CUSTOMER_SUPPORT_EMAIL = 'customer support email'
    LIST_LIKE_OUTPUTS = [BUSINESS_OPERATION, SELLS_THROUGH, GEOGRAPHICAL_AREAS, WHEN_CUSTOMER_MAKES_A_PAYMENT, DIRECT_SALES_CHANNELS,
                         BILLING_MODELS, TERMS_COVERAGE, INSURANCE_OPTIONS]
    MERCHANT_NAME = 'merchant_name'
    ORDER_FOR_UI = [MERCHANT_NAME, DESCRIPTION, INDUSTRY, DIRECT_SALES_CHANNELS, BUSINESS_OPERATION, SELLS_THROUGH, BILLING_MODELS,
                    GEOGRAPHICAL_AREAS, WHEN_CUSTOMER_MAKES_A_PAYMENT, TERMS_COVERAGE, INSURANCE_OPTIONS, CUSTOMER_SUPPORT_EMAIL]

class ResponseCategories:
    INDUSTRIES: List[str] = ['retail', 'financial services', 'travel', 'gaming', 'crypto', 'software subscription', 'gambling', 'ticketing', 'delivery']
    INDUSTRIES_STR: str = str(INDUSTRIES).replace("'", "")
    BUSINESS_OPERATIONS: List[str] = ['Marketplace', 'On-Demand Service Platform', 'Reseller', 'Drop-shipping', 'Franchise', 'OTA']
    BUSINESS_OPERATIONS_STR: str = str(BUSINESS_OPERATIONS).replace("'", "")
    GEOGRAPHICAL_AREAS: List[str] = ['North America', 'Latin America', 'Europe', 'Middle East', 'Africa', 'Asia']
    GEOGRAPHICAL_AREAS_STR: str = str(GEOGRAPHICAL_AREAS).replace("'", "")
    PAYMENT_RESPONSE: List[str] = ['Topping-Up Account Balance', 'Purchasing']
    PAYMENT_RESPONSE_STR: str = str(PAYMENT_RESPONSE).replace("'", "")
    DIRECT_SALES_CHANNELS: List[str] = ['Website', 'Mobile app', '3rd party', 'Phone calls']
    DIRECT_SALES_CHANNELS_STR: str = str(DIRECT_SALES_CHANNELS).replace("'", "")
    BILLING_MODELS: List[str] = ['One time payment', 'Subscriptions', 'Installments']
    BILLING_MODELS_STR: str = str(BILLING_MODELS).replace("'", "")
    TERMS_COVERAGE: List[str] = ['Cancellation Policy', 'Return Policy', 'Refund Policy', 'Exchange Policy', 'Warranty Policy',
                                 'Delivery terms and timeframes', 'Disclaimers about the product / service',
                                 'Subscription / Recurring charges', 'Subscription automatic renewal', 'Non-refundable charges',
                                 'Payments schedule', 'Support availability', 'Force Majeure', 'Item is sold \'AS-IS\'',
                                 'Negative option terms', 'Industry regulations', 'Insurance']
    TERMS_COVERAGE_STR: str = str(TERMS_COVERAGE).replace("'", "")
    INSURANCE_OPTIONS: List[str] = ['Shipping Protection', 'Product Protection', 'Extended Warranty']
    INSURANCE_OPTIONS_STR: str = str(INSURANCE_OPTIONS).replace("'", "")


class QuestionnairePrompts:
    GENERAL: str = f'From the information in this website, and what you know about this merchant, ' \
                   f'answer the following three questions and return a json in the following format: ' \
                   f'{{{OUTPUTS.COMPANY}: <Search the company name. Return the answer as a string.>, ' \
                   f'{OUTPUTS.DESCRIPTION}: <Describe the company in a few sentences. Describe in details what does the company sell / offer> ' \
                   f'{OUTPUTS.INDUSTRY}: <See this list of one-word industry descriptions: {ResponseCategories.INDUSTRIES_STR}. ' \
                   f'Choose one description that suits the provided company the most based on the company description. ' \
                   f'You can only use the options provided above, and do not add explanations.>,' \
                   f'{OUTPUTS.BUSINESS_OPERATION}: <See this list of business operations: {ResponseCategories.BUSINESS_OPERATIONS_STR}. ' \
                   f'choose only the options the provided company operates its business at. {REDUCE_HELLUCINATIONS_STR}>,' \
                   f'{OUTPUTS.SELLS_THROUGH}: <See this list of third party options: {ResponseCategories.BUSINESS_OPERATIONS_STR}. ' \
                   f'choose only the options the provided company sells its products through if their are any. {REDUCE_HELLUCINATIONS_STR}>,' \
                   f'{OUTPUTS.GEOGRAPHICAL_AREAS}: <See this list of geographical areas: {ResponseCategories.GEOGRAPHICAL_AREAS_STR}. ' \
                   f'choose only the options the provided company operate in. {REDUCE_HELLUCINATIONS_STR}>, ' \
                   f'{OUTPUTS.WHEN_CUSTOMER_MAKES_A_PAYMENT}: <See this list of consequences of making a payment: {ResponseCategories.PAYMENT_RESPONSE_STR}. ' \
                   f'choose only the options that can occur when a customer makes a payment at the merchant. {REDUCE_HELLUCINATIONS_STR}>}}'
    ADVANCED: str = f'From the information in this website, and what you know about this merchant, ' \
                    f'answer the following three questions and return a json in the following format: ' \
                    f'{{{OUTPUTS.DIRECT_SALES_CHANNELS}: <See this list of selling channel options: {ResponseCategories.DIRECT_SALES_CHANNELS_STR}. ' \
                    f'Choose only the options the provided company uses to sell their products. {REDUCE_HELLUCINATIONS_STR}>, ' \
                    f'{OUTPUTS.BILLING_MODELS}: <See this list of billing model options: {ResponseCategories.BILLING_MODELS_STR}. ' \
                    f'Choose only the options the provided company offers. {REDUCE_HELLUCINATIONS_STR}>,' \
                    f'{OUTPUTS.TERMS_COVERAGE}: <See this list of topics: {ResponseCategories.TERMS_COVERAGE_STR}. ' \
                    f'Choose only the topics that are covered by the companys\' terms. {REDUCE_HELLUCINATIONS_STR}>, ' \
                    f'{OUTPUTS.INSURANCE_OPTIONS}: <See this list of insurance options: {ResponseCategories.INSURANCE_OPTIONS_STR}. ' \
                    f'Choose only the options that are offered by the company. {REDUCE_HELLUCINATIONS_STR}>, ' \
                    f'{OUTPUTS.CUSTOMER_SUPPORT_EMAIL}: <What is the merchant customer support email? Return the answer as a string. ' \
                    f'If you can not find it, return NULL>}}'
    DESCRIPTION: str = 'From the information in this website, and what you know about this merchant, ' \
                       'answer the following three questions and return a json in the following format: ' \
                       '{company: answer_to_question_1, ' \
                       'description: answer_to_question_2, ' \
                       'long_description: answer_to_question_3}. ' \
                       '1. Search the company name. Return the answer as a string. ' \
                       '2. Describe the company in up to five sentences, and no less than three ' \
                       'sentences. Focus on what they do as a company, and what services they offer. ' \
                       'Be neutral and descriptive. Return the answer as a string ' \
                       '3.Describe the company in a few sentences. Describe in details what does the company sell\offer.'
    OFFERINGS: str = 'See this list of offerings descriptions: ' \
                     '"Physical Goods, Digital Goods, Software, In-Person Services, Personal Banking, Payment Facilitation, Investment Services, Accommodation, Top Up Services, Crypto Currencies, Gaming, Gambling, NFTs, Hotels, Car Rentals, Flights, Tickets". ' \
                     'Choose only the primary offerings that ' \
                     'suits the provided company the most based on the company description. You can only use the options provided ' \
                     'above, dont invent other options. Return a json in the following format: {offerings: [OFFERING_A, OFFERING_B]}.'
    INDUSTRY: str = 'See this list of one-word industry descriptions: ' \
                    '"Retail, Financial Services, Travel, Gaming, Crypto, Software Subscription, Gambling, Ticketing, Delivery". ' \
                    'Choose one description that suits the provided company the most based on the company description. You can ' \
                    'only use the options provided above, dont invent other options. Return a json in the following format: {industry: INDUSTRY}.'
    CHANNELS_BILLINGS_DELIVERY_EMAIL: str = 'From the information in this website, answer the following four questions and return the answers in a json format: ' \
                                            '{channels: answer_to_question_1, ' \
                                            'billings: answer_to_question_2, ' \
                                            'delivery_methods: answer_to_question_3,' \
                                            'emailAddress: answer_to_question_4}. ' \
                                            'If the text from the website does not contain required information to answer ' \
                                            'the question return "NULL". Dont answer based on your previous knowledge. ' \
                                            '1. See this list of selling channel options: "Website, Mobile app, 3rd party, Phone calls". ' \
                                            'Based on the information on the website, choose only the options the provided ' \
                                            'company uses to sell their products. You can only choose out the options provided above, ' \
                                            'dont invent other options. Return the answer as a list of strings ' \
                                            '2. See this list of billing models: "One time payment, Subscriptions, Installments". ' \
                                            'out of this list, choose only the options the provided company offers. ' \
                                            'You can only choose out the options provided above, dont invent other options. ' \
                                            'Choose as many answers as applicable, but not options that are not listed. Return the answer as a list of strings. ' \
                                            '3. Does the merchant sell physical things? ' \
                                            'If the merchant doesnt sell physical things return ["Merchant doesnt sell physical goods"]. ' \
                                            'If he does, what delivery methods does the seller offer? Shipping, in store pickup or other? ' \
                                            'Return the answer as a list of strings. ' \
                                            '4. What is the merchant customer support email? Return the answer as a string.'
    POLICIES: str = 'From the information in this website, answer the following three questions and return the answers in a json format: ' \
                    '{cancellation: answer_to_question_1, ' \
                    'refund_policy: answer_to_question_2, ' \
                    'return_policy: answer_to_question_3}. ' \
                    'If the text from the website does not contain required information to answer the question replace ' \
                    'X with "NULL". Dont answer based on your previous knowledge. ' \
                    '1.Summarize the cancellation policy on the website. Mention the specific conditions for cancellation. ' \
                    'Provide the relevant quotes from the website and the URL for the source you use for your answer. ' \
                    'Return the answer as a json in this format: {summary: X, quote: X , source: X}' \
                    '2. Summarize the exact conditions to get a refund based on the information from the website. return it as a string. ' \
                    '3. What is the maximum number of days for return? Summarize the exact conditions based on the information from the website. return it as a string.'
    CRYPTO: str = 'From the information in this website answer the following question. Does the platform use ' \
                 'blockchain to transfer the crypto or the crypto transfer is done on it’s own platform? if the ' \
                 'merchant industry is not crypto return NULL. ' \
                 'Return the answer as a json in this format: {crypto_transfers: blockchain\internal system}'
    LIABILITY: str = 'Based on the information on the website, who takes liability on the following topics? ' \
                     'Chargebacks (fraud transactions and service), delivery issues and product quality? ' \
                     'Return the answer as a json in this format: ' \
                     '{Chargebacks: X, delivery_issues: X, quality: X}. ' \
                     'If this information is missing, replace X with NULL.'


class ResponseCategories:
    OFFERINGS: List[str] = field(default_factory=lambda: ['physical goods, digital goods, software, in-person services, in person services, personal banking, '
                      'payment facilitation, investment services, accommodation, top up services, '
                      'crypto currencies, gaming, gambling, nfts, hotels, car rentals, flights, tickets'])
    INDUSTRIES: List[str] = ['retail', 'financial services', 'travel', 'gaming', 'crypto', 'software subscription', 'gambling', 'ticketing', 'delivery']
