from typing import List, Dict, Tuple, Union
from openai import OpenAI
# needed locally
import os
from dotenv import load_dotenv
load_dotenv()


class RFPLlmAnswerer:
    SYSTEM_PROMPT = "I work at Justt.ai. A fintech company that handles chargebacks automatically for merchants. " \
             "I want you to fill the best answer you can on my behalf to questions for an RFP for new merchants. " \
             "I will supply previous questions and answers we made for other merchants, and want you to answer the last one. " \
                    "Reply only the answer. Do not use the names of other merchants."

    def __init__(self, openai_api_key: str = None):
        openai_api_key = openai_api_key if openai_api_key is not None else os.getenv(key='OPENAI_API_KEY')
        self.openai_client = OpenAI(api_key=openai_api_key)

    def build_prompt(self, similar_questions: List[Dict[str, str]], question: str, merchant_name: str = "_____") -> str:
        user_prompt = f"merchant name for the RFP: {merchant_name}. Previous questions and answers:\n"
        for q_a in similar_questions:
            user_prompt += f"Question: {q_a['question']}\n Answer: {q_a['answer']}\n\n"
        user_prompt += f"Question to answer: {question}\n Answer:"
        return user_prompt

    def generate_answer(self, similar_questions: List[Dict[str, str]], question: str, merchant_name: str = "_____", return_prompt=False) \
            -> Union[str, Tuple[str, List]]:
        user_prompt = self.build_prompt(similar_questions, question, merchant_name)
        messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        completion = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        if return_prompt:
            return completion.choices[0].message.content, messages
        else:
            return completion.choices[0].message.content
