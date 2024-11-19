from typing import List, Dict, Tuple, Union
from openai import OpenAI
# needed locally
import os
from dotenv import load_dotenv
load_dotenv()


class RFPLlmAnswerer:
    """
    A class that uses OpenAI's language models to generate answers for RFP (Request for Proposal) questions
    based on previous Q&A pairs. Specifically designed for Justt.ai's chargeback handling service context.

    Attributes:
        SYSTEM_PROMPT (str): The system prompt that provides context about Justt.ai and the task
        openai_client (OpenAI): The OpenAI client instance for making API calls
    """
    SYSTEM_PROMPT = "I work at Justt.ai. A fintech company that handles chargebacks automatically for merchants. " \
             "I want you to fill the best answer you can on my behalf to questions for an RFP for new merchants. " \
             "I will supply previous questions and answers we made for other merchants, and want you to answer the last one. " \
                    "Reply only the answer. Do not use the names of other merchants."

    def __init__(self, openai_api_key: str = None):
        """
        Initialize the RFP LLM Answerer with OpenAI credentials.

        Args:
            openai_api_key (str, optional): OpenAI API key. If None, will attempt to load from environment
                variables using 'OPENAI_API_KEY'.
        """
        openai_api_key = openai_api_key if openai_api_key is not None else os.getenv(key='OPENAI_API_KEY')
        self.openai_client = OpenAI(api_key=openai_api_key)

    def build_prompt(self, similar_questions: List[Dict[str, str]], question: str, merchant_name: str = "_____") -> str:
        """
        Construct the prompt for the language model using previous Q&A pairs and the current question.

        Args:
            similar_questions (List[Dict[str, str]]): List of dictionaries containing previous Q&A pairs.
                Each dictionary should have 'question' and 'answer' keys.
            question (str): The current question to be answered.
            merchant_name (str, optional): Name of the merchant for whom the RFP is being prepared.
                Defaults to "_____".

        Returns:
            str: The constructed prompt string containing the merchant name, previous Q&A pairs,
                and the current question.

        Example:
            >> similar_questions = [{"question": "What is your SLA?", "answer": "24 hours"}]
            >> question = "What is your response time?"
            >> answerer.build_prompt(similar_questions, question, "ACME Corp")
            "merchant name for the RFP: ACME Corp. Previous questions and answers:
             Question: What is your SLA?
             Answer: 24 hours

             Question to answer: What is your response time?
             Answer:"
        """
        user_prompt = f"merchant name for the RFP: {merchant_name}. Previous questions and answers:\n"
        for q_a in similar_questions:
            user_prompt += f"Question: {q_a['question']}\n Answer: {q_a['answer']}\n\n"
        user_prompt += f"Question to answer: {question}\n Answer:"
        return user_prompt

    def generate_answer(self, similar_questions: List[Dict[str, str]], question: str, merchant_name: str = "_____", return_prompt=False) \
            -> Union[str, Tuple[str, List]]:
        """
        Generate an answer for an RFP question using OpenAI's language model and previous Q&A pairs.

        The method constructs a prompt using previous Q&A pairs and the current question,
        then uses OpenAI's GPT model to generate a contextually appropriate answer.

        Args:
            similar_questions (List[Dict[str, str]]): List of dictionaries containing previous Q&A pairs.
                Each dictionary should have 'question' and 'answer' keys.
            question (str): The current question to be answered.
            merchant_name (str, optional): Name of the merchant for whom the RFP is being prepared.
                Defaults to "_____".
            return_prompt (bool, optional): If True, returns both the generated answer and the complete
                prompt used for generation. Defaults to False.

        Returns:
            Union[str, Tuple[str, List]]: If return_prompt is False, returns just the generated answer
                as a string. If return_prompt is True, returns a tuple containing the generated answer
                and the list of messages used in the prompt.

        Example:
            >> similar_questions = [{"question": "What is your SLA?", "answer": "24 hours"}]
            >> question = "What is your response time?"
            >> answer = answerer.generate_answer(similar_questions, question)
            >> print(answer)
            "Our standard response time is within 24 hours of receiving a chargeback notification."
        """
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
