import streamlit as st
from get_response_func import get_questionnaire_responses, get_response_single_prompt
import ast
import pandas as pd

st.header("AI-BOARDING :scream_cat: :100:")

st.radio(
    "",
    ["Get response by URL", "Try it yourself"],
    key="mode",
    label_visibility='hidden',
    horizontal=True,
)

if st.session_state.mode == "Get response by URL":

    st.markdown("Use this tool to collect information about the merchant as part of the onboarding research. "
             "Just fill in the merchant's website and click go! \n")
    st.markdown("Note: The information reliability must be verified (AI can get creative)")
    st.markdown("**Your feedback is appreciated!** At the bottom you will find a CSV template, download it and fill in the following: \n")
    st.markdown("like_or_dislike \n")
    st.markdown("comments: comments you have about the tool outputs \n")
    st.markdown("suggestion: suggestions for prompt improvement")
    st.markdown("Upload the CSV file to: https://drive.google.com/drive/folders/17TlhsWgsRqcForpTxrxosWLGd5BrZRF1?usp=drive_link")

    st.text_input("URL", key="URL")

    st.text_input("Additional URLs", key="additional_urls")

    # access the value
    url = st.session_state.URL
    additional_urls = st.session_state.additional_urls.replace(" ", "").split(",")
    additional_urls = [i for i in additional_urls if i]

    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            width: 300px;
            height: 50px;
            font-size: 40px;
            display: flex;
            margin: auto;
            background-color: #2E8B57;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    if st.button('GO!'):

        responses, questions = get_questionnaire_responses(url, additional_urls)

        st.subheader(f"**URL:** {url}")
        merchant_name = responses["merchant_name"]
        description = responses["description"]
        industry = responses["industry"]
        channels = responses["channels"]
        billings = responses["billings"]
        email_address = responses["emailAddress"]
        customer_support = responses["customer_support"]
        cancellation = responses["cancellation"]
        refund_policy = responses["refund_policy"]
        delivery_methods = responses["delivery_methods"]
        liability = responses["liability"]

        st.subheader("Merchant name")
        st.write(merchant_name)

        st.subheader("Merchant description")
        st.write(description)

        st.subheader("Industry")
        st.write(industry)

        st.subheader("channels")
        st.write(channels)

        st.subheader("billings")
        st.write(billings)

        st.subheader("email_address")
        st.write(email_address)

        st.subheader("customer_support")
        st.write(customer_support)

        st.subheader("cancellation")
        st.write(cancellation)

        st.subheader("refund_policy")
        st.write(refund_policy)

        st.subheader("delivery_methods")
        st.write(delivery_methods)

        st.subheader("liability")
        st.write(liability)

        # st.subheader("crypto_transfers")
        # st.write(crypto_transfers)

        st.divider()
        df = pd.DataFrame({"question": pd.Series(["merchant_name", "description", "industry", "channels",
                                                  "billings", "email_address", "customer_support", "cancellation",
                                                  "refund_policy", "delivery_methods", "liability"]),
                           "response": pd.Series([merchant_name, description, industry, channels,
                                                  billings, email_address, customer_support, cancellation,
                                                  refund_policy, delivery_methods, liability]),
                           "like_or_dislike": None,
                           "comments": None,
                           "suggestion": None})

        st.download_button(
            "Download as a CSV",
            df.to_csv(index=False).encode('utf-8'),
            "file.csv",
            "text/csv",
            key='download-csv'
        )
        st.dataframe(df)


if st.session_state.mode == "Try it yourself":
    st.write(f"We welcome new prompt suggestions :blush:, feel free to post them here: https://drive.google.com/drive/folders/1kv4nwb49IhfOl6-SHu-sBZjCH7mtLs3A?usp=drive_link")
    st.text_input("Prompt", key="prompt")
    st.markdown(
            """
            <style>
            div.stButton > button:first-child {
                width: 300px;
                height: 50px;
                font-size: 40px;
                display: flex;
                margin: auto;
                background-color: #2E8B57;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    if st.button('Try it yourself!'):
        single_response = get_response_single_prompt(st.session_state.prompt)
        st.write(f"**prompt**")
        st.write(st.session_state.prompt)
        st.write(f"**response**")
        st.write(single_response)
