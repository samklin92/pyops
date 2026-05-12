import os
import anthropic
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path


# Initialize embedding model and vector store
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.Client()
collection = client.create_collection("runbooks")


def load_runbooks(runbooks_dir="runbooks"):
    docs = []
    for path in Path(runbooks_dir).glob("*.md"):
        content = path.read_text(encoding="utf-8")
        docs.append({
            "id": path.stem,
            "content": content,
            "filename": path.name
        })
    return docs


def index_runbooks(docs):
    for doc in docs:
        embedding = model.encode(doc["content"]).tolist()
        collection.add(
            ids=[doc["id"]],
            embeddings=[embedding],
            documents=[doc["content"]],
            metadatas=[{"filename": doc["filename"]}]
        )
    print(f"Indexed {len(docs)} runbooks")


def search_runbooks(query, top_k=2):
    query_embedding = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results["documents"][0]


def analyse_with_context(query, infra_summary):
    # Step 1 — retrieve relevant runbooks
    relevant_docs = search_runbooks(query)
    context = "\n\n---\n\n".join(relevant_docs)

    # Step 2 — call Claude with runbook context
    llm_client = anthropic.Anthropic()

    message = llm_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=f"""You are an expert DevOps engineer.
You have access to the following runbooks from the operations knowledge base:

{context}

Use these runbooks to provide specific, actionable recommendations.
Always reference the relevant runbook steps in your response.""",
        messages=[
            {
                "role": "user",
                "content": f"Analyse this infrastructure and provide recommendations:\n{infra_summary}"
            }
        ]
    )

    return message.content[0].text


if __name__ == "__main__":
    # Load and index runbooks
    docs = load_runbooks()
    index_runbooks(docs)

    # Infrastructure summary
    infra_summary = """
- i-0abc123 | t3.micro | us-east-1 | CPU: 82% | ALERT
- i-0def456 | t3.large | us-west-2 | CPU: 45% | OK
- i-0ghi789 | t3.medium | eu-west-1 | CPU: 91% | ALERT
- i-0jkl012 | t3.small | ap-southeast-1 | CPU: 60% | OK
"""

    query = "high CPU utilization on EC2 instances"

    print("=== RAG-Powered Infrastructure Analysis ===\n")
    response = analyse_with_context(query, infra_summary)
    print(response)