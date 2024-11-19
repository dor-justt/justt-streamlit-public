from typing import List, Union
import glob
import os
from pathlib import Path
import pandas as pd
from rfp.rfp_constants import CSV_FORMAT

import logging


def load_csv(file_path: str) -> pd.DataFrame:
    """
    Load and process an RFP CSV file into a standardized DataFrame format.

    This function performs several transformations:
    1. Loads the CSV file with all columns as strings
    2. Adds a comment column if missing
    3. Filters out invalid rows (those with missing required fields)
    4. Constructs unique IDs using filename and row numbers
    5. Combines category and question fields when applicable
    6. Merges answers and comments
    7. Creates a formatted text field combining questions and answers

    Args:
        file_path (str): Path to the CSV file to load

    Returns:
        pd.DataFrame: Processed DataFrame with columns:
            - id: Unique identifier (filename + row number)
            - Question: Combined category and question text
            - Answer: Combined answer and comment text
            - txt: Formatted question-answer pair

    Example:
        >> df = load_csv("rfp_responses.csv")
        >> print(df.columns)
        ['id', 'Question', 'Answer', 'txt']
    """
    logging.info(f"loading csv: {file_path}")
    df = pd.read_csv(file_path, dtype=str)

    # Add comment column if missing
    if CSV_FORMAT.COMMENT not in df.columns:
        df[CSV_FORMAT.COMMENT] = pd.NA

    # Filter out invalid rows
    mask = pd.isna(df[CSV_FORMAT.NUMBER]) | pd.isna(df[CSV_FORMAT.QUESTION]) | (pd.isna(df[CSV_FORMAT.ANSWER]) & pd.isna(df[CSV_FORMAT.COMMENT]))
    for i, row in df.loc[mask].iterrows():
        logging.info(f"Row containing NaN at file path {file_path}, number {row[CSV_FORMAT.NUMBER]}. Content: {row}")
        continue
    df = df[~mask]

    # Create result DataFrame with standardized format
    result_df = pd.DataFrame(columns=['id', 'Question', 'Answer', 'txt'])
    result_df['id'] = os.path.basename(file_path)+df[CSV_FORMAT.NUMBER]
    result_df['Question'] = df.apply(lambda row: row[CSV_FORMAT.QUESTION] if
                            (pd.isna(row[CSV_FORMAT.CATEGORY]) or row[CSV_FORMAT.CATEGORY] in ('None', 'NaN', '')) else
                            ': '.join([row[CSV_FORMAT.CATEGORY], row[CSV_FORMAT.QUESTION]]), axis=1)
    result_df['Answer'] = df.apply(lambda row: _add_comment(row[CSV_FORMAT.ANSWER], row[CSV_FORMAT.COMMENT]), axis=1)
    result_df['txt'] = result_df.apply(lambda row: _format_question_and_answer_string(row['Question'], row['Answer']), axis=1)
    return result_df


def load_rfp_files_dir(dir_path: Union[Path, str]) -> pd.DataFrame:
    """
    Load and combine all CSV files in a directory into a single DataFrame.

    Args:
        dir_path (Union[Path, str]): Path to directory containing RFP CSV files

    Returns:
        pd.DataFrame: Combined DataFrame containing data from all CSV files in the directory,
            with the same structure as the output of load_csv()

    Example:
        >> df = load_rfp_files_dir("path/to/rfp/files")
        >> print(f"Loaded {len(df)} total QA pairs")
    """
    csv_files: List = glob.glob(os.path.join(dir_path, "*.csv"))
    logging.info(csv_files)
    df_list: List[pd.DataFrame] = []
    for file_path in csv_files:
        df_list.append(load_csv(file_path))
    return pd.concat(df_list, ignore_index=True)


def _add_comment(answer: str, comment: str) -> str:
    """
    Combine an answer and its comment into a single string, handling punctuation
    and empty values appropriately.

    Args:
        answer (str): The main answer text
        comment (str): Additional comment text

    Returns:
        str: Combined answer and comment text with appropriate punctuation

    Examples:
        >> _add_comment("We offer 24/7 support", "Available in all time zones")
        "We offer 24/7 support. Available in all time zones"
        >> _add_comment("We offer 24/7 support.", "Available in all time zones")
        "We offer 24/7 support. Available in all time zones"
        >>> _add_comment("", "Comment only")
        "Comment only"
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
    """
    Format a question-answer pair into a standardized string format.

    Args:
        question (str): The question text
        answer (str): The answer text

    Returns:
        str: Formatted string with question and answer on separate lines

    Example:
        >> _format_question_and_answer_string("What is your SLA?", "24 hours")
        "Question: What is your SLA?\nAnswer: 24 hours"
    """
    return f"Question: {question}\nAnswer: {answer}"


# Main execution
if __name__ == "__main__":
    # Step 1: Embed all existing RFP files
    rfp_directory = "rfp_files"
    p = load_rfp_files_dir(rfp_directory)
    print(p)
