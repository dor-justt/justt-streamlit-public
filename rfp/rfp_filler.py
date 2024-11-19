from typing import List, Dict, Any, Union, Tuple
from rfp.rfp_pinecone_embedder import RFPPinceconeEmbedder
from rfp.rfp_llm_answerer import RFPLlmAnswerer


class RFPFiller:
    """
    A class that combines vector similarity search and language model capabilities
    to automatically answer RFP (Request for Proposal) questions based on previous Q&A pairs.

    The class uses Pinecone for similarity search to find relevant previous answers
    and a language model to generate contextually appropriate responses.

    Attributes:
        rfp_pinecone_embedder (RFPPinceconeEmbedder): Component for vector similarity search
        rfp_llm_answerer (RFPLlmAnswerer): Component for language model-based answer generation
    """
    def __init__(self, pinecone_api_key: str = None, pinecone_rfp_index: str = None, openai_api_key: str = None):
        """
        Initialize the RFP Filler with necessary API keys and components.

        Args:
            pinecone_api_key (str, optional): API key for Pinecone vector database.
                If None, will try to use environment variable.
            pinecone_rfp_index (str, optional): Name of the Pinecone index to use.
                If None, will try to use environment variable.
            openai_api_key (str, optional): API key for OpenAI services.
                If None, will try to use environment variable.
        """
        self.rfp_pinecone_embedder = RFPPinceconeEmbedder(pinecone_api_key, pinecone_rfp_index)
        self.rfp_llm_answerer = RFPLlmAnswerer(openai_api_key)

    def answer_question(self, question: str, merchant_name: str = "____", return_prompt=False) -> Union[str, Tuple[str, List]]:
        """
        Generate an answer for a given RFP question using similar previous Q&A pairs.

        The method works by:
        1. Finding similar previous questions using vector similarity search
        2. Using these similar Q&A pairs as context for the language model
        3. Generating a new, contextually appropriate answer

        Args:
            question (str): The RFP question to be answered
            merchant_name (str, optional): Name of the merchant to be used in the answer.
                Defaults to "____".
            return_prompt (bool, optional): If True, returns both the generated answer
                and the prompt used to generate it. Defaults to False.

        Returns:
            Union[str, Tuple[str, List]]: If return_prompt is False, returns just the
                generated answer as a string. If return_prompt is True, returns a tuple
                containing the generated answer and the prompt used to generate it.
        """
        similar_questions_matches: List[Dict[str, Any]] = self.rfp_pinecone_embedder.get_matches(question)
        q_a: List[Dict[str, str]] = [m['metadata'] for m in similar_questions_matches]
        response = self.rfp_llm_answerer.generate_answer(q_a, question, merchant_name, return_prompt=return_prompt)
        return response
