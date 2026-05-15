from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid

# Must match ingest.py exactly
COLLECTION_NAME = "ops_runbooks"
EMBEDDING_DIM = 384
CORPUS_DIR = Path(__file__).parent.parent.parent / "rag" / "corpus"

model = SentenceTransformer("all-MiniLM-L6-v2")


def build_qdrant_client() -> QdrantClient:
    """Ingest corpus and return a ready Qdrant client."""
    qdrant = QdrantClient(":memory:")

    if not qdrant.collection_exists(COLLECTION_NAME):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )

    all_chunks = []
    for md_file in CORPUS_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8")

        # Strip code fences
        lines = []
        in_code_block = False
        for line in text.splitlines():
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            lines.append(line)
        clean_text = "\n".join(lines)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=64,
            separators=["\n\n", "\n", " "]
        )

        for chunk in splitter.split_text(clean_text):
            if chunk.strip():
                all_chunks.append({
                    "text": chunk.strip(),
                    "source": md_file.name
                })

    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=False).tolist()

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"text": chunk["text"], "source": chunk["source"]}
        )
        for chunk, embedding in zip(all_chunks, embeddings)
    ]

    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    return qdrant


def search_runbooks(query: str, qdrant_client: QdrantClient, top_k: int = 3) -> list[dict]:
    query_embedding = model.encode([query], show_progress_bar=False).tolist()[0]

    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k
    ).points

    return [
        {
            "text": hit.payload["text"],
            "source": hit.payload["source"],
            "score": round(hit.score, 3)
        }
        for hit in results
    ]


# Tool schema for the LLM
RAG_SEARCH_TOOL = {
    "name": "search_runbooks",
    "description": (
        "Search internal runbooks and operational documentation for known issues, "
        "remediation steps, and procedures. Use this after querying metrics to find "
        "matching known issues and recommended fixes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query e.g. 'ECS task restarting' or 'ALB 502 errors'"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return. Default 3.",
                "default": 3
            }
        },
        "required": ["query"]
    }
}