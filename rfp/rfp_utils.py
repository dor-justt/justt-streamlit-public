from typing import List, Union
import glob
import os
from pathlib import Path
import pandas as pd
from rfp_constants import CSV_FORMAT

import logging


def load_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, dtype=str)
    if CSV_FORMAT.COMMENT not in df.columns:
        df[CSV_FORMAT.COMMENT] = pd.NA
    mask = pd.isna(df[CSV_FORMAT.NUMBER]) | pd.isna(df[CSV_FORMAT.QUESTION]) | (pd.isna(df[CSV_FORMAT.ANSWER]) & pd.isna(df[CSV_FORMAT.COMMENT]))
    for i, row in df.loc[mask].iterrows():
        logging.info(f"Row containing NaN at file path {file_path}, number {row[CSV_FORMAT.NUMBER]}. Content: {row}")
        continue
    df = df[~mask]
    result_df = pd.DataFrame(columns=['id', 'Question', 'Answer', 'txt'])
    result_df['id'] = os.path.basename(file_path)+df[CSV_FORMAT.NUMBER]
    result_df['Question'] = df.apply(lambda row: row[CSV_FORMAT.QUESTION] if
                            (pd.isna(row[CSV_FORMAT.CATEGORY]) or row[CSV_FORMAT.CATEGORY] in ('None', 'NaN', '')) else
                            ': '.join([row[CSV_FORMAT.CATEGORY], row[CSV_FORMAT.QUESTION]]), axis=1)
    result_df['Answer'] = df.apply(lambda row: _add_comment(row[CSV_FORMAT.ANSWER], row[CSV_FORMAT.COMMENT]), axis=1)
    result_df['txt'] = result_df.apply(lambda row: _format_question_and_answer_string(row['Question'], row['Answer']), axis=1)
    return result_df


def load_rfp_files_dir(dir_path: Union[Path, str]) -> pd.DataFrame:
    csv_files: List = glob.glob(os.path.join(dir_path, "*.csv"))
    logging.info(csv_files)
    df_list: List[pd.DataFrame] = []
    for file_path in csv_files:
        df_list.append(load_csv(file_path))
    return pd.concat(df_list, ignore_index=True)


def _add_comment(answer: str, comment: str) -> str:
    """
    Adds the comment to the answer.
    :param answer:
    :param comment:
    :return: a string with both the answer and the comment.
    """
    comment = comment if pd.notna(comment) else ""
    answer = answer if pd.notna(answer) else ""
    answer = answer.rstrip()
    if len(answer) == 0 or len(comment) == 0:
        return f"{answer}{comment}"
    if answer[-1] == '.':
        return f"{answer} {comment}"
    return f"{answer}. {comment}"


def _format_question_and_answer_string(question: str, answer: str) -> str:
    return f"Question: {question}\nAnswer: {answer}"


# Main execution
if __name__ == "__main__":
    # Step 1: Embed all existing RFP files
    rfp_directory = "rfp_files"
    p = load_rfp_files_dir(rfp_directory)
    print(p)
