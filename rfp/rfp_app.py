import streamlit as st

from rfp_filler import RFPFiller

rfp_fil = RFPFiller()


def main():
    st.title('Justt RFP & VRA replier')

    # st.text_input("Question", key="MERCHANT_NAME")
    st.markdown(
        """
        <style>
        div.stButton > button:first-child {
            width: 400px;
            height: 60px;
            font-size: 40px;
            display: flex;
            margin: auto;
            background-color: #006400;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    merchant_name = st.text_input("merchant name (optional)", '')
    question = st.text_input("Question")
    if st.button("GO!", key="go_button") and question is not None:
        merchant_name = merchant_name if merchant_name != '' else "_____"
        with st.spinner('Thinking...'):
            answer, prompt = rfp_fil.answer_question(question, merchant_name, return_prompt=True)

        dic = {'Answer': answer, 'System prompt': prompt[0]['content'], 'user prompt': prompt[1]['content']}
        names = list(dic.keys())
        tabs = st.tabs(names)
        for t, name in zip(tabs, names):
            with t:
                st.write(dic[name])


if __name__ == '__main__':
    main()
