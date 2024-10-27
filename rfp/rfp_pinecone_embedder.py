import pandas as pd

from pinecone import Pinecone, QueryResponse
from sentence_transformers import SentenceTransformer

from rfp_constants import CSV_FORMAT

# needed locally
import os
from dotenv import load_dotenv
load_dotenv()


class RFPPinceconeEmbedder:
    EMBEDDING_MODEL = 'multi-qa-mpnet-base-dot-v1'
    TOP_K = 20

    def __init__(self, pinecone_api_key: str = None, pinecone_rfp_index: str = None):
        pinecone_api_key = pinecone_api_key if pinecone_api_key is not None else os.getenv(key='PINECONE_API_KEY')
        pinecone_rfp_index = pinecone_rfp_index if pinecone_rfp_index is not None else os.getenv(key='PINECONE_RFP_INDEX')
        pc = Pinecone(api_key=pinecone_api_key)
        self.index = pc.Index(pinecone_rfp_index)
        self.model = SentenceTransformer(self.EMBEDDING_MODEL)

    def upsert_question(self, embedding_id, question, answer):
        question_embedding = self._generate_embedding(question)
        values = {
            "id": str(embedding_id),
            "values": question_embedding,
            "metadata": {"question": question, "answer": answer}
        }
        self.index.upser(values)

    def upsert_csv(self, file_path):
        df = pd.read_csv(file_path, dtype=str)
        # if 'owe' not in file_path:
        #     print('continuing')
        #     return
        embeddings = []
        batch_size = 100
        for i, row in df.iterrows():
            if pd.isna(row[CSV_FORMAT.NUMBER]) or pd.isna(row[CSV_FORMAT.QUESTION]) or \
                    (pd.isna(row[CSV_FORMAT.ANSWER]) and pd.isna(row[CSV_FORMAT.COMMENT])):
                print(f"Row containing NaN at row number {i}. Content: {row}")
                continue
            category = "" if pd.isna(row[CSV_FORMAT.CATEGORY]) or row[CSV_FORMAT.CATEGORY] in ('None', 'NaN') else row[CSV_FORMAT.CATEGORY]
            if category != "":
                question = ': '.join([row[CSV_FORMAT.CATEGORY], row[CSV_FORMAT.QUESTION]])
            else:
                question = row[CSV_FORMAT.QUESTION]
            comment = row[CSV_FORMAT.COMMENT]
            answer = row[CSV_FORMAT.ANSWER]
            answer = self._add_comment(answer, comment)
            number = row[CSV_FORMAT.NUMBER]
            question_embedding = self._generate_embedding(self._format_question_and_answer_string(question, answer))

            embeddings.append({
                "id": f"{os.path.basename(file_path)}_{number}",
                "values": question_embedding,
                "metadata": {"question": question, "answer": answer}
            })

            if len(embeddings) >= batch_size:
                self.index.upsert(embeddings)
                embeddings = []
        # Upsert any remaining embeddings
        if len(embeddings) > 0:
            self.index.upsert(embeddings, namespace='questionnaires')

    def get_matches(self, question):
        # get the vector of embeddings
        embedding = self._generate_embedding(question)
        # QueryResponse is a dictionary with 3 keys: matches, namespace, usage.
        # The 'matches' value is a list of the matches. Each value is a dictionary with 'id', 'metadata', 'score', 'values'.
        similar_questions: QueryResponse = self._search_similar(embedding)
        return similar_questions['matches']

    def _search_similar(self, query_embedding, top_k=20):
        return self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True, namespace='questionnaires')

    def _generate_embedding(self, text):
        return self.model.encode(text).tolist()

    @staticmethod
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
        if answer[-1] == '.':
            return f"{answer} {comment}"
        return f"{answer}. {comment}"

    @staticmethod
    def _format_question_and_answer_string(question: str, answer: str) -> str:
        return f"Question: {question}\nAnswer: {answer}"


def embed_all_rfps(directory, rfp_pc_embedder):
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            print(f"Processing {filename}...")
            rfp_pc_embedder.upsert_csv(file_path)


# Main execution
if __name__ == "__main__":
    rfp_pc_embedder = RFPPinceconeEmbedder()
    # Step 1: Embed all existing RFP files
    rfp_directory = "rfp_files"
    print("Embedding existing RFP files...")
    embed_all_rfps(rfp_directory, rfp_pc_embedder)
    print("Finished embedding existing RFP files.")
