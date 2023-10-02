from typing import Tuple, Dict
import pandas as pd
from dataclasses import fields

from hotel_pdf_parser_constants import FIELD_NAMES


class DataPostProcessor:

    @staticmethod
    def post_process(extracted_data: Dict[str, str], chargeback_id: str = '') -> Tuple[Dict[str, str], pd.DataFrame]:
        processed_result = {getattr(FIELD_NAMES, f.name).outer: extracted_data.get(getattr(FIELD_NAMES, f.name).inner, '') for f in
                            fields(FIELD_NAMES)}
        processed_result[FIELD_NAMES.CHARGEBACK_ID.outer] = chargeback_id
        df = pd.Series(processed_result).to_frame().T
        return processed_result, df
