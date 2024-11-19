from typing import List
import argparse
import pandas as pd
import uuid
from pathlib import Path
from pinecone import Pinecone, QueryResponse
from pinecone_text.sparse import BM25Encoder, SparseVector
from pinecone_text.hybrid import hybrid_convex_scale
from sentence_transformers import SentenceTransformer
from rfp.rfp_utils import load_csv, load_rfp_files_dir, _format_question_and_answer_string
import os
import logging
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)


class RFPPinceconeEmbedder:
    """
    A class for embedding RFP (Request for Proposal) questions and answers using Pinecone vector database.
    Implements hybrid search using both dense and sparse embeddings for improved retrieval performance.

    Attributes:
        DENSE_EMBEDDING_MODEL (str): Name of the pre-trained sentence transformer model for dense embeddings
        SPARSE_EMBEDDING_PARAMETERS_PATH (str): Path to save/load BM25 parameters
        TOP_K (int): Default number of similar results to return
        ALPHA (float): Weight factor between dense and sparse vector search (0 to 1)
    """
    DENSE_EMBEDDING_MODEL = 'multi-qa-mpnet-base-dot-v1'  # https://sbert.net/docs/sentence_transformer/pretrained_models.html
    SPARSE_EMBEDDING_PARAMETERS_PATH = 'bm25_params.json'
    TOP_K = 20
    ALPHA = 0.5  # for weighting between the dense and the sparse vector search

    def __init__(self, pinecone_api_key: str = None, pinecone_rfp_index: str = None):
        """
        Initialize the RFP embedder with Pinecone credentials and embedding models.

        Args:
            pinecone_api_key (str, optional): Pinecone API key. Defaults to environment variable.
            pinecone_rfp_index (str, optional): Name of Pinecone index. Defaults to environment variable.
        """
        pinecone_api_key = pinecone_api_key if pinecone_api_key is not None else os.getenv(key='PINECONE_API_KEY')
        pinecone_rfp_index = pinecone_rfp_index if pinecone_rfp_index is not None else os.getenv(key='PINECONE_RFP_INDEX')
        pc = Pinecone(api_key=pinecone_api_key)
        self.index = pc.Index(pinecone_rfp_index)
        self.dense_model = SentenceTransformer(self.DENSE_EMBEDDING_MODEL)
        self.sparse_model = BM25Encoder()
        file_path = Path(__file__).parent / self.SPARSE_EMBEDDING_PARAMETERS_PATH
        if file_path.exists():
            self.sparse_model.load(file_path)
            logging.info(f'Sparse model loaded.')
        else:
            logging.info('Sparse model not loaded')

    def upsert_question(self, question: str, answer: str, embedding_id: str = None):
        """
        Insert or update a single question-answer pair in the Pinecone index.

        Args:
            question (str): The question text
            answer (str): The answer text
            embedding_id (str, optional): Custom ID for the embedding. If None, generates a unique ID.

        Returns:
            dict: Pinecone upsert response
        """
        embeddings = []
        txt = _format_question_and_answer_string(question, answer)
        question_dense_embedding = self._generate_dense_embedding(txt)
        question_sparse_embedding = self._generate_sparse_embedding(txt)
        if embedding_id is None:
            embedding_id = self._generate_id()
        embeddings.append({
            "id": str(embedding_id),
            "values": question_dense_embedding,
            "sparse_values": question_sparse_embedding,
            "metadata": {"question": question, "answer": answer}
        })
        response = self.index.upsert(embeddings, namespace='questionnaires')
        return response

    def _generate_id(self, max_attempts=10):
        for _ in range(max_attempts):
            # Generate a new UUID and convert to string
            new_id = 'user_input_'+str(uuid.uuid4())

            # Check if ID exists in index
            fetch_response = self.index.fetch(ids=[new_id])

            # If the ID doesn't exist in the index (empty vectors returned), return it
            if not fetch_response.vectors:
                return new_id

        raise RuntimeError(f"Failed to generate unique ID after {max_attempts} attempts")

    def upsert_df(self, df: pd.DataFrame):
        """
        Batch insert or update questions and answers from a DataFrame.

        Args:
            df (pd.DataFrame): DataFrame containing 'txt', 'id', 'Question', and 'Answer' columns
        """
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
        self.upsert_df(df)

    def get_matches(self, question: str, alpha: float = 0.9):
        """
        Find similar questions using hybrid search (dense + sparse embeddings).

        Args:
            question (str): Query question text
            alpha (float): Weight between dense (alpha) and sparse (1-alpha) similarities

        Returns:
            list: List of matching documents with their similarity scores and metadata
        """
        # get the vector of embeddings
        dense_embedding = self._generate_dense_embedding(question)
        sparse_embedding = self.sparse_model.encode_queries(question)
        dense_embedding, sparse_embedding = hybrid_convex_scale(dense_embedding, sparse_embedding, alpha=alpha)
        # QueryResponse is a dictionary with 3 keys: matches, namespace, usage.
        # The 'matches' value is a list of the matches. Each value is a dictionary with 'id', 'metadata', 'score', 'values'.
        similar_questions: QueryResponse = self._search_similar(dense_embedding, sparse_embedding)
        return similar_questions['matches']

    def _search_similar(self, query_dense_embedding, query_sparse_embedding, top_k=20):
        """
        Execute hybrid search query in Pinecone.

        Args:
            query_dense_embedding: Dense vector embedding of the query
            query_sparse_embedding: Sparse vector embedding of the query
            top_k (int): Number of results to return

        Returns:
            QueryResponse: Pinecone query response containing matches
        """
        return self.index.query(vector=query_dense_embedding, sparse_vector=query_sparse_embedding, top_k=top_k, include_metadata=True,
                                namespace='questionnaires')

    def _generate_dense_embedding(self, text) -> List[float]:
        """
        Generate dense embedding vector for input text.

        Args:
            text (str): Input text to embed

        Returns:
            List[float]: Dense embedding vector
        """
        return self.dense_model.encode(text).tolist()

    def _generate_sparse_embedding(self, text) -> SparseVector:
        """
        Generate sparse embedding vector for input text.

        Args:
            text (str): Input text to embed

        Returns:
            SparseVector: Sparse embedding vector
        """
        return self.sparse_model.encode_documents(text)

    def retrain_sparse_model(self, directory_path, save_model=True):
        """
        Retrain the sparse embedding model on new data.

        Args:
            directory_path (str): Path to directory containing training data
            save_model (bool): Whether to save the retrained model parameters
        """
        df = load_rfp_files_dir(directory_path)
        self.sparse_model.fit(df['txt'])
        if save_model:
            self.sparse_model.dump(self.SPARSE_EMBEDDING_PARAMETERS_PATH)
            logging.info("sparse model saved")


def embed_rfp_files(files_path, rfp_pc_embedder):
    """
    Load and embed RFP files into Pinecone index.

    Args:
        files_path (str): Path to directory containing RFP files or CSV file
        rfp_pc_embedder (RFPPinceconeEmbedder): Initialized embedder instance

    Raises:
        ValueError: If the path is neither a directory nor a CSV file
    """
    path_obj = Path(files_path)
    if path_obj.is_dir():
        df = load_rfp_files_dir(path_obj)
    elif path_obj.is_file() and path_obj.suffix == '.csv':
        df = load_csv(path_obj)
    else:
        raise ValueError("The path added is neither an existing directory or a valid csv file")
    rfp_pc_embedder.upsert_df(df)


def main(args):
    logging.info(f"rfp_pinecone_embedder with train_sparse_model: {args.train_sparse_model}, update_pinecone_embedding: {args.update_pinecone_embedding}")
    rfp_directory = args.rfp_files_dir
    rfp_pc_embedder = RFPPinceconeEmbedder()
    if args.train_sparse_model:
        rfp_pc_embedder.retrain_sparse_model(rfp_directory)
    if args.update_pinecone_embedding:
        logging.info("Embedding existing RFP files...")
        embed_rfp_files(rfp_directory, rfp_pc_embedder)
        logging.info("Finished embedding existing RFP files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for running and/or retraining the embedder")
    parser.add_argument(
        "--rfp_files_dir",
        help="rfp_files_dir",
        required=True,
        type=str,
        default="rfp_files"
    )
    parser.add_argument(
        "--train_sparse_model",
        help="used to specify if the sparse model should be retrained",
        action="store_true",  # will default to false if flag is not present
    )
    parser.add_argument(
        "--update_pinecone_embedding",
        help="used to update all the pinecone embedding. Occurs after the sparse retraining (if marked)",
        action="store_true",  # will default to false if flag is not present
    )
    arguments = parser.parse_args()
    main(arguments)

