from typing import Tuple, List
import re
import pdf2image
import pytesseract
from stqdm import stqdm


class PDFPreprocessor:
    CHUNK_SIZE = 3500
    CHUNK_OVERLAP = 300

    @staticmethod
    def preprocess_pdf(pdf_file) -> Tuple[str, List[str]]:
        image_list = PDFPreprocessor._bytes2imagelist(pdf_file)
        extracted_text = PDFPreprocessor._imagelist2text(image_list)
        # print("cleaning")
        clean_text = PDFPreprocessor._clean_text(extracted_text)
        # print("chunking")
        chunks = PDFPreprocessor._get_chunks(clean_text)
        return clean_text, chunks


    @staticmethod
    def _bytes2imagelist(pdf_file) -> List:
        return pdf2image.convert_from_bytes(pdf_file.getbuffer())

    @staticmethod
    def _imagelist2text(image_list: List) -> str:
        entire_text = ''
        for pagenumber in stqdm(range(len(image_list)), desc="Extracting text by page"):
            detected_text = pytesseract.image_to_string(image_list[pagenumber])  # config = config
            entire_text += detected_text
        return entire_text

    @staticmethod
    def _clean_text(txt: str) -> str:
        res = txt
        res = re.sub('\nPage(.*?)\n', '', res)
        res = re.sub('\nDocuSign(.*?)\n', '', res)
        res = re.sub('\n([^\n]{1,2})\n', '', res)
        return res

    @staticmethod
    def _get_chunks(input_string, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> List[str]:
        chunks = []
        temp_str = input_string
        while len(temp_str) > 0:
            chunks.append(temp_str[:chunk_size])
            temp_str = temp_str[chunk_size - overlap:]
        return chunks
