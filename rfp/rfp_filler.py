from typing import List, Dict, Any, Union, Tuple
from rfp_pinecone_embedder_v2 import RFPPinceconeEmbedder
from rfp_llm_answerer import RFPLlmAnswerer


class RFPFiller:
    def __init__(self, pinecone_api_key: str = None, pinecone_rfp_index: str = None, openai_api_key: str = None):
        self.rfp_pinecone_embedder = RFPPinceconeEmbedder(pinecone_api_key, pinecone_rfp_index)
        self.rfp_llm_answerer = RFPLlmAnswerer(openai_api_key)

    def answer_question(self, question: str, merchant_name: str = "____", return_prompt=False) -> Union[str, Tuple[str, List]]:
        similar_questions_matches: List[Dict[str, Any]] = self.rfp_pinecone_embedder.get_matches(question)
        q_a: List[Dict[str, str]] = [m['metadata'] for m in similar_questions_matches]
        response = self.rfp_llm_answerer.generate_answer(q_a, question, merchant_name, return_prompt=return_prompt)
        return response
