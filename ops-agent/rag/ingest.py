from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid

# Local embedding model — no API key needed
model = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient(":memory:")

COLLECTION_NAME = "ops_runbooks"
EMBEDDING_DIM = 384
CORPUS_DIR = Path(__file__).parent / "corpus"


def embed(texts: list[str]) -> list[list[float]]:
    return model.encode(texts, show_progress_bar=False).tolist()


def chunk_markdown(file_path: Path) -> list[dict]:
    """
    Single-pass chunking — strips code fences first to avoid
    markdown splitter breaking on triple backticks.
    """
    text = file_path.read_text(encoding="utf-8")

    # Strip code fences — preserve the content inside them
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

    chunks = []
    for chunk in splitter.split_text(clean_text):
        if chunk.strip():
            chunks.append({
                "text": chunk.strip(),
                "metadata": {"source": file_path.name}
            })

    return chunks


def ingest_corpus():
    # Fix deprecation warning
    if not qdrant.collection_exists(COLLECTION_NAME):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
    else:
        qdrant.delete_collection(COLLECTION_NAME)
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )

    print(f"Collection '{COLLECTION_NAME}' created.\n")

    all_chunks = []
    for md_file in CORPUS_DIR.glob("*.md"):
        chunks = chunk_markdown(md_file)
        print(f"{md_file.name}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"\nTotal chunks: {len(all_chunks)}")
    print("Embedding and uploading to Qdrant...")

    texts = [c["text"] for c in all_chunks]
    embeddings = embed(texts)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": chunk["text"],
                **chunk["metadata"]
            }
        )
        for chunk, embedding in zip(all_chunks, embeddings)
    ]

    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Uploaded {len(points)} chunks to Qdrant.\n")

    return qdrant


def search_runbooks(query: str, qdrant_client: QdrantClient, top_k: int = 3) -> list[dict]:
    query_embedding = embed([query])[0]

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


if __name__ == "__main__":
    qdrant_client = ingest_corpus()

    test_queries = [
        "ECS task keeps restarting",
        "ALB returning 502 errors",
        "CloudWatch alarm not sending notification",
        "GitHub Actions ECR push failing"
    ]

    print("--- Retrieval Test ---\n")
    for query in test_queries:
        print(f"Query: {query}")
        results = search_runbooks(query, qdrant_client)
        for r in results:
            print(f"  [{r['score']}] {r['source']} — {r['text'][:100]}...")
        print()