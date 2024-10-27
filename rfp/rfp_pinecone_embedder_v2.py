from typing import List, Dict, Union
import pandas as pd
from pathlib import Path
from pinecone import Pinecone, QueryResponse
from pinecone_text.sparse import BM25Encoder, SparseVector
from pinecone_text.hybrid import hybrid_convex_scale
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from rfp_constants import CSV_FORMAT
from rfp_utils import load_csv, load_rfp_files_dir
# needed locally
import os
import logging
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)


class RFPPinceconeEmbedder:
    DENSE_EMBEDDING_MODEL = 'multi-qa-mpnet-base-dot-v1'  # https://sbert.net/docs/sentence_transformer/pretrained_models.html
    SPARSE_EMBEDDING_PARAMETERS_PATH = 'bm25_params.json'
    TOP_K = 20
    ALPHA = 0.5  # for weighting between the dense and the sparse vector search

    def __init__(self, pinecone_api_key: str = None, pinecone_rfp_index: str = None):
        pinecone_api_key = pinecone_api_key if pinecone_api_key is not None else os.getenv(key='PINECONE_API_KEY')
        pinecone_rfp_index = pinecone_rfp_index if pinecone_rfp_index is not None else os.getenv(key='PINECONE_RFP_INDEX')
        pc = Pinecone(api_key=pinecone_api_key)
        self.index = pc.Index(pinecone_rfp_index)
        self.dense_model = SentenceTransformer(self.DENSE_EMBEDDING_MODEL)
        self.sparse_model = BM25Encoder()
        file_path = Path(__file__).parent / self.SPARSE_EMBEDDING_PARAMETERS_PATH
        print(file_path)
        if file_path.exists():
            self.sparse_model.load(file_path)
            logging.info(f'Sparse model loaded.')
        else:
            logging.info('Sparse model not loaded')

    def upsert_question(self, embedding_id, question, answer):
        question_embedding = self._generate_dense_embedding(question)
        values = {
            "id": str(embedding_id),
            "values": question_embedding,
            "metadata": {"question": question, "answer": answer}
        }
        self.index.upser(values)

    def upsert_df(self, df: pd.DataFrame):
        embeddings = []
        batch_size = 100
        for i, row in df.iterrows():
            question_dense_embedding = self._generate_dense_embedding(row['txt'])
            question_sparse_embedding = self._generate_sparse_embedding(row['txt'])
            embeddings.append({
                "id": row['id'],
                "values": question_dense_embedding,
                "sparse_values": question_sparse_embedding,
                "metadata": {"question": row['Question'], "answer": row['Answer']}
            })

            if len(embeddings) >= batch_size:
                self.index.upsert(embeddings)
                embeddings = []
        # Upsert any remaining embeddings
        if len(embeddings) > 0:
            self.index.upsert(embeddings, namespace='questionnaires')

    def upsert_csv(self, file_path):
        df = load_csv(file_path)
        embeddings = []
        batch_size = 100
        for i, row in tqdm(df.iterrows(), total=df.shape[0]):
            question_dense_embedding = self._generate_dense_embedding(row['txt'])
            question_sparse_embedding = self._generate_sparse_embedding(row['txt'])
            embeddings.append({
                "id": row['id'],
                "values": question_dense_embedding,
                "sparse_values": question_sparse_embedding,
                "metadata": {"question": row['Question'], "answer": row['Answer']}
            })

            if len(embeddings) >= batch_size:
                self.index.upsert(embeddings)
                embeddings = []
        # Upsert any remaining embeddings
        if len(embeddings) > 0:
            self.index.upsert(embeddings, namespace='questionnaires')

    def get_matches(self, question: str, alpha: float = 0.7):
        # get the vector of embeddings
        dense_embedding = self._generate_dense_embedding(question)
        sparse_embedding = self.sparse_model.encode_queries(question)
        dense_embedding, sparse_embedding = hybrid_convex_scale(dense_embedding, sparse_embedding, alpha=alpha)
        # QueryResponse is a dictionary with 3 keys: matches, namespace, usage.
        # The 'matches' value is a list of the matches. Each value is a dictionary with 'id', 'metadata', 'score', 'values'.
        similar_questions: QueryResponse = self._search_similar(dense_embedding, sparse_embedding)
        return similar_questions['matches']

    def _search_similar(self, query_dense_embedding, query_sparse_embedding, top_k=20):
        return self.index.query(vector=query_dense_embedding, sparse_vector=query_sparse_embedding, top_k=top_k, include_metadata=True,
                                namespace='questionnaires')

    def _generate_dense_embedding(self, text) -> List[float]:
        return self.dense_model.encode(text).tolist()

    def _generate_sparse_embedding(self, text) -> SparseVector:
        return self.sparse_model.encode_documents(text)

    def retrain_sparse_model(self, directory_path, save_model=True):
        df = load_rfp_files_dir(directory_path)
        self.sparse_model.fit(df['txt'])
        if save_model:
            self.sparse_model.dump(self.SPARSE_EMBEDDING_PARAMETERS_PATH)
            logging.info("sparse model saved")


def embed_rfp_files(files_path, rfp_pc_embedder):
    path_obj = Path(files_path)
    if path_obj.is_dir():
        df = load_rfp_files_dir(path_obj)
    elif path_obj.is_file() and path_obj.suffix == '.csv':
        df = load_csv(path_obj)
    else:
        raise ValueError("The path added is neither an existing directory or a valid csv file")
    rfp_pc_embedder.upsert_df(df)

# import nltk
# nltk.download('punkt_tab')
# Main execution


if __name__ == "__main__":
    rfp_pc_embedder = RFPPinceconeEmbedder()
    # Step 1: Embed all existing RFP files
    rfp_directory = "rfp_files"
    # rfp_pc_embedder.retrain_sparse_model(rfp_directory)
    print("Embedding existing RFP files...")
    embed_rfp_files(rfp_directory, rfp_pc_embedder)
    print("Finished embedding existing RFP files.")
