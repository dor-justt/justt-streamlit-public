from typing import List

OPENAI_MODEL = "gpt-4o-mini"  # "gpt-3.5-turbo-16k"
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
                   f'You can only use the options provided above, and do not add explanations. Note that retail industry includes ' \
                   f'businesses that sell a variety of goods and services directly to consumers, often through both physical and online ' \
                   f'stores.>. The gaming industry includes companies that develop, publish, and distribute video games and ' \
                   f'gaming-related products and services.>, ' \
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
