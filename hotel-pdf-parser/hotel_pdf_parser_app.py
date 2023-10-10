import streamlit as st

from pdf_preprocessor import PDFPreprocessor
from data_extractor import DataExtractor
from data_post_processor import DataPostProcessor


def main():
    st.title('Justt Hotel PDF parser')

    uploaded_file = st.file_uploader("Choose a file")
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
    chargeback_id = st.text_input("chargebackId", '')
    if st.button("GO!", key="go_button") and uploaded_file is not None:

        # Preprocess result
        extracted_text, chunks = PDFPreprocessor.preprocess_pdf(uploaded_file)

        # LLM
        with st.spinner('Querying the LLM...'):
            result = DataExtractor.extract_data(chunks)

        # process result
        processed_result, df = DataPostProcessor.post_process(result, chargeback_id=chargeback_id)

        # Explanations
        dic = {'Results': processed_result, 'Raw results': result, 'Extracted text': extracted_text}
        names = list(dic.keys())
        tabs = st.tabs(names)
        for t, name in zip(tabs, names):
            with t:
                st.write(dic[name])

        # to csv
        file_name = chargeback_id if len(chargeback_id) > 0 else '___'
        db = st.download_button(
            "Download as a CSV",
            df.to_csv(index=False).encode('utf-8'),
            f"{file_name}.csv",
            "text/csv",
            key='download-csv',
            )


if __name__ == '__main__':
    main()
