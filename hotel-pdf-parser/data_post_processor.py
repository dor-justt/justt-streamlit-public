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
        processed_result = DataPostProcessor._verify_names(processed_result)
        df = pd.Series(processed_result).to_frame().T
        return processed_result, df

    @staticmethod
    def _verify_names(processed_result) -> Dict[str, str]:
        # fill first name by full name
        if len(processed_result[FIELD_NAMES.GUEST_FULL_NAME.outer]) > 0 and processed_result[FIELD_NAMES.GUEST_FIRST_NAME.outer] == "":
            processed_result[FIELD_NAMES.GUEST_FIRST_NAME.outer] = processed_result[FIELD_NAMES.GUEST_FULL_NAME.outer].split()[0]

        # fill last name by full name
        if len(processed_result[FIELD_NAMES.GUEST_FULL_NAME.outer]) > 0 and processed_result[FIELD_NAMES.GUEST_LAST_NAME.outer] == "":
            processed_result[FIELD_NAMES.GUEST_FIRST_NAME.outer] = processed_result[FIELD_NAMES.GUEST_FULL_NAME.outer].split()[-1]

        # fill full name by first and last name
        if len(processed_result[FIELD_NAMES.GUEST_FULL_NAME.outer]) == 0:
            # use both first and last name
            if len(processed_result[FIELD_NAMES.GUEST_FIRST_NAME.outer]) > 0 and \
                    len(processed_result[FIELD_NAMES.GUEST_LAST_NAME.outer]) > 0:
                processed_result[FIELD_NAMES.GUEST_FULL_NAME.outer] = processed_result[FIELD_NAMES.GUEST_FIRST_NAME.outer] + " " + \
                                                                      processed_result[FIELD_NAMES.GUEST_LAST_NAME.outer]
            # use first name only
            elif len(processed_result[FIELD_NAMES.GUEST_FIRST_NAME.outer]) > 0 and \
                    len(processed_result[FIELD_NAMES.GUEST_LAST_NAME.outer]) == 0:
                processed_result[FIELD_NAMES.GUEST_FULL_NAME.outer] = processed_result[FIELD_NAMES.GUEST_FIRST_NAME.outer]
            # use last name only
            elif len(processed_result[FIELD_NAMES.GUEST_FIRST_NAME.outer]) == 0 and \
                    len(processed_result[FIELD_NAMES.GUEST_LAST_NAME.outer]) > 0:
                processed_result[FIELD_NAMES.GUEST_FULL_NAME.outer] = processed_result[FIELD_NAMES.GUEST_LAST_NAME.outer]

        return processed_result
