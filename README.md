# PyOps — Python for DevOps Toolkit

A production-grade AI-powered infrastructure monitoring tool built with Python, Boto3, FastAPI, RAG, and an AI agent with tool calling.

---

## What It Does

- Monitors real AWS EC2 instances via Boto3
- Pulls live CPU metrics from CloudWatch
- Stores timestamped reports in S3
- Exposes infrastructure data via a REST API (FastAPI)
- Searches operations runbooks using RAG (ChromaDB + sentence transformers)
- Runs an AI agent that autonomously analyses infrastructure and generates remediation plans
- Full pytest test suite

---

## Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.14 |
| AWS | Boto3 — EC2, CloudWatch, S3 |
| API | FastAPI + uvicorn |
| AI | Anthropic Claude (claude-sonnet-4-6) |
| RAG | ChromaDB + sentence-transformers |
| Testing | pytest |

---

## Project Structure

```
pyops/
├── infra/
│   ├── config.py       — config loader (JSON)
│   ├── instance.py     — EC2Instance class
│   ├── monitor.py      — InfraMonitor class
│   ├── reporter.py     — S3Reporter (upload, list, download)
│   └── __init__.py
├── tests/
│   ├── test_instance.py
│   └── test_monitor.py
├── runbooks/           — markdown runbooks for RAG
├── agent.py            — AI agent with tool calling
├── api.py              — FastAPI REST API
├── aws_monitor.py      — live AWS monitoring script
├── rag_pipeline.py     — RAG pipeline (load, index, search)
├── main.py             — entry point (mock data)
├── config.json         — environment configuration
└── README.md
```

---

## Configuration

`config.json`:

```json
{
    "environment": "production",
    "region": "us-east-1",
    "instance_type": "t3.micro",
    "min_replicas": 2,
    "max_replicas": 10,
    "alert_threshold": 75,
    "s3_bucket": "pyops-infra-reports-109804294707"
}
```

---

## Setup

```bash
git clone https://github.com/samklin92/pyops.git
cd pyops
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install boto3 fastapi uvicorn pytest anthropic chromadb sentence-transformers
aws configure
```

---

## Usage

**Run mock monitor:**
```bash
python main.py
```

**Run live AWS monitor:**
```bash
python aws_monitor.py
```

**Start API:**
```bash
uvicorn api:app --reload
```

**Run agent directly:**
```bash
python agent.py
```

**Run tests:**
```bash
pytest
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status |
| GET | `/health` | Health check |
| GET | `/instances` | Live EC2 instances with CPU data |
| GET | `/reports` | List S3 reports |
| GET | `/reports/latest` | Fetch latest report content |
| POST | `/agent/query` | Run AI agent with natural language query |

**Example agent query:**
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Analyse the current AWS infrastructure in us-east-1 and provide a prioritised remediation plan"}'
```

---

## AI Agent Tools

The agent (`agent.py`) has access to 5 tools:

| Tool | Description |
|------|-------------|
| `get_ec2_instances` | Fetch real EC2 instances from AWS |
| `get_cloudwatch_cpu` | Fetch CPU utilization from CloudWatch |
| `analyse_instance` | Assess health status per instance |
| `search_runbooks` | RAG search over operations runbooks |
| `save_report` | Persist report to S3 |

**Agent loop:**
```
Instruction → EC2 → CloudWatch → Analyse → Runbooks → S3 Report → Response
```

---

## Learning Roadmap

This project was built as a structured 12-week learning plan across three phases.

### Phase 1 — Python & AWS Foundations (Sessions 1–8)

| Session | Topic | Output |
|---------|-------|--------|
| 1 | Python basics — variables, types, control flow | `basics.py` |
| 2 | Functions, error handling, file I/O | `file_io.py`, `error_test.py` |
| 3 | OOP — classes, methods, inheritance | `oop_basics.py`, `infra_oop.py` |
| 4 | Logging and config management | `logger_test.py`, `read_config.py` |
| 5 | Boto3 — EC2 describe, launch, terminate | `boto3_test.py`, `launch_instance.py`, `terminate_instance.py` |
| 6 | Boto3 — S3 upload, list, download | `s3_test.py`, `infra/reporter.py` |
| 7 | Boto3 — CloudWatch metrics | `aws_monitor.py` |
| 8 | pytest — unit testing the infra package | `tests/` (13 tests) |

### Phase 2 — API & AI Integration (Sessions 9–14)

| Session | Topic | Output |
|---------|-------|--------|
| 9 | FastAPI — REST API with EC2 and S3 | `api.py` — `/health`, `/instances`, `/reports` |
| 10 | LLM basics — Anthropic API, prompt engineering | `llm_test.py`, `llm_ops.py` |
| 11 | Structured LLM output — JSON responses | `llm_structured.py` |
| 12 | RAG pipeline — ChromaDB, embeddings, runbook search | `rag_pipeline.py`, `runbooks/` |
| 13 | AI agent — tool calling, multi-step reasoning | `agent.py` |
| 14 | FastAPI agent endpoint — HTTP interface to agent | `api.py` — `POST /agent/query` |

### Phase 3 — Production & MLOps (Sessions 15–20) — Planned

| Session | Topic |
|---------|-------|
| 15 | Dockerise the API and agent |
| 16 | Deploy to AWS ECS or EKS |
| 17 | CI/CD pipeline with GitHub Actions |
| 18 | Terraform infrastructure for the stack |
| 19 | Observability — structured logging, metrics, tracing |
| 20 | Capstone — full production deployment |

---

## Capstone Projects

| Phase | Project |
|-------|---------|
| Phase 1 | Live AWS infrastructure monitor with S3 reporting |
| Phase 2 | AI-powered ops agent with FastAPI interface |
| Phase 3 | Production-deployed AI monitoring platform on AWS |
