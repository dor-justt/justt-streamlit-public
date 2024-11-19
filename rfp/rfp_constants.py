from dataclasses import dataclass


@dataclass(frozen=True)
class CSV_FORMAT:
    NUMBER = 'Number'
    CATEGORY = 'Category'
    QUESTION = 'Question'
    ANSWER = 'Answer'
    COMMENT = 'Comment'


