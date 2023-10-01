import streamlit as st

from pdf_preprocessor import PDFPreprocessor
from data_extractor import DataExtractor


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
    if st.button("GO!", key="go_button") and uploaded_file is not None:
        extracted_text, chunks = PDFPreprocessor.preprocess_pdf(uploaded_file)
        result = DataExtractor.extract_data(chunks)
        # Explanations
        names = ['Results', 'Extracted text']
        tabs = st.tabs(['Results', 'Extracted text'])
        dic = {'Results': result, 'Extracted text': extracted_text}
        for t, name in zip(tabs, names):
            with t:
                st.write(dic[name])


if __name__ == '__main__':
    main()
