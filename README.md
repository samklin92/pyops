# PyOps — Python DevOps Toolkit

A production-grade infrastructure monitoring tool built with Python, Boto3, and FastAPI.

## What it does
- Monitors real AWS EC2 instances via Boto3
- Pulls live CPU metrics from CloudWatch
- Stores timestamped reports in S3
- Exposes infrastructure data via a REST API (FastAPI)
- Full pytest test suite (13 tests passing)

## Stack
- Python 3.14
- Boto3 — EC2, CloudWatch, S3
- FastAPI + uvicorn
- pytest
- AWS (EC2, S3, CloudWatch)

## Project Structure

```
infra/
├── config.py       — config loading
├── instance.py     — EC2Instance class
├── monitor.py      — InfraMonitor class
└── reporter.py     — S3 reporting
tests/
├── test_instance.py
└── test_monitor.py
api.py              — FastAPI REST API
aws_monitor.py      — live AWS monitoring script
main.py             — entry point
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install boto3 fastapi uvicorn pytest
aws configure
python main.py
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | API status |
| `GET /instances` | Live EC2 data |
| `GET /reports` | S3 report listing |
| `GET /reports/latest` | Latest monitor output |