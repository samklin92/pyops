# PyOps API — Phase 1 Capstone

A production-grade containerised FastAPI application deployed on AWS ECS Fargate with a full CI/CD pipeline, HTTPS endpoint, and observability stack.

## Architecture

<img width="1536" height="1024" alt="aws cloud infrastructure" src="https://github.com/user-attachments/assets/4603f312-56f1-46ef-9a56-e89798ae73ba" />


## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI + Uvicorn |
| Container Registry | AWS ECR |
| Orchestration | AWS ECS Fargate |
| Load Balancer | AWS ALB |
| TLS | AWS ACM |
| DNS | Namecheap → api.samklin.online |
| CI/CD | GitHub Actions |
| Observability | CloudWatch Dashboards + Alarms |
| Alerting | SNS → Email |

## Project Structure

```
python-devops/
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD pipeline
├── infra/
│   ├── task-def.json         # ECS task definition
│   └── dashboard.json        # CloudWatch dashboard
├── tests/                    # pytest test suite
├── api.py                    # FastAPI application
├── main.py                   # Entry point
├── Dockerfile                # Container build
├── requirements.txt          # Python dependencies
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Health check — returns API status |
| GET | /health | Version and status response |

## Live Endpoint

```
https://api.samklin.online
https://api.samklin.online/health
```

## CI/CD Pipeline

Every push to `main` triggers:
1. Docker image build
2. Image tagged with git SHA and pushed to ECR
3. ECS service force-redeployed with new image

## Observability

- **Dashboard:** CloudWatch — ECS CPU, Memory, ALB request count, 5xx errors
- **Alarms:**
  - ECS CPU > 80% for 2 consecutive minutes
  - ECS Memory > 80% for 2 consecutive minutes
  - ALB 5xx errors > 5 per minute
- **Alerting:** SNS topic → email notification

## Infrastructure

- **ECS Cluster:** `pyops-cluster`
- **ECS Service:** `pyops-api-svc` (Fargate, 1 task, 256 CPU / 512 MB)
- **ECR Repository:** `pyops-api`
- **ALB:** `pyops-api-alb` (internet-facing)
- **Target Group:** `pyops-api-tg` (health check on `/health`)
- **Certificate:** ACM — `api.samklin.online`
- **CloudWatch Dashboard:** `pyops-dashboard`
