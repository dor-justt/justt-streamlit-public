import streamlit as st

from pdf_preprocessor import PDFPreprocessor
from data_extractor import DataExtractor
from data_post_processor import DataPostProcessor


def main():
    st.title('Justt Hotel PDF parser')

    uploaded_file = st.file_uploader("Choose a file")
    
    engine = st.radio(
        "Parsing engine",
        [
            "OCR (Tesseract) + OpenAI",
            "NVIDIA OCR + OpenAI",
            "NVIDIA (Vision-to-JSON, no OCR)",
        ],
        index=0,
        horizontal=True
        )
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
        
        use_nvidia =  engine=="NVIDIA OCR + OpenAI"
        use_only_nvidia = engine=="NVIDIA (Vision-to-JSON, no OCR)"
        
        # step 1+2: preprocess the pdf and extract the text using NVIDIA VLM
        if use_only_nvidia:
            with st.spinner('Vision-to-JSON with NVIDIA VLM...'):
                image_list = PDFPreprocessor._bytes2imagelist(uploaded_file)
                # 1) load PDF as images
                if not image_list:
                    st.error("No images/pages found in the uploaded file.")
                    return

                # 2) call VLM to get JSON
                result = DataExtractor.extract_data_nvidia_vlm(image_list)

                # 3) no extracted text in this path (we skipped OCR by design)
                extracted_text = "(skipped: direct vision-to-JSON with NVIDIA VLM)"
                chunks = ["(skipped)"]  # to keep downstream happy
        else:
            # step 1: preprocess the pdf
            with st.spinner(f'Parsing PDF with {"NVIDIA" if use_nvidia else "Tesseract OCR"}....'):
                    extracted_text, chunks = PDFPreprocessor.preprocess_pdf(
                        uploaded_file,
                        use_nvidia=use_nvidia
                    )

            if not chunks:
                st.error("No chunks found")
                return
            
            # step 2: query the LLM
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
