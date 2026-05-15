# PyOps — Python DevOps Toolkit

A production-grade infrastructure automation platform built on AWS. Phase 1 delivers a containerised FastAPI service with a full CI/CD pipeline. Phase 2 delivers a reusable Boto3 automation toolkit, a CLI, and a comprehensive test suite.

---

## Architecture

```
git push → GitHub Actions (pytest gate) → ECR → ECS Fargate (Phase 3)
                                                       ↓
internet → api.samklin.online (HTTPS) → ALB → Target Group → ECS Task
                                                       ↓
                                       CloudWatch → Dashboard → Alarms → SNS → Email
```

---

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI + Uvicorn |
| Container Registry | AWS ECR |
| Orchestration | AWS ECS Fargate |
| Load Balancer | AWS ALB |
| TLS | AWS ACM |
| DNS | api.samklin.online |
| CI/CD | GitHub Actions |
| Observability | CloudWatch Dashboards + Alarms |
| Alerting | SNS → Email |
| AWS Automation | Boto3 |
| Testing | pytest + unittest.mock |
| Coverage | 98% |

---

## Project Structure

```
python-devops/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD — pytest gate + ECS deploy
├── infra/
│   ├── task-def.json           # ECS task definition
│   └── dashboard.json          # CloudWatch dashboard config
├── tests/
│   ├── conftest.py             # Shared fixtures, mock heavy deps
│   ├── test_api.py             # API endpoint tests
│   ├── test_toolkit.py         # Toolkit unit tests
│   ├── test_instance.py        # EC2Instance model tests
│   └── test_monitor.py         # InfraMonitor tests
├── toolkit/
│   ├── __init__.py
│   ├── ec2.py                  # EC2 automation
│   ├── s3.py                   # S3 automation
│   ├── iam.py                  # IAM automation
│   └── monitor.py              # CloudWatch automation
├── api.py                      # FastAPI application
├── cli.py                      # PyOps CLI
├── agent.py                    # AI ops agent
├── Dockerfile                  # Container build
├── requirements.txt            # Python dependencies
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | API status |
| GET | /health | Version and health check |
| GET | /instances | List all EC2 instances |
| GET | /instances/running | List running instances only |
| GET | /instances/{id} | Get instance state |
| POST | /instances/{id}/stop | Stop an instance |
| POST | /instances/{id}/start | Start an instance |
| GET | /reports | List S3 reports |
| GET | /reports/latest | Get latest report content |
| GET | /alarms | List CloudWatch alarms |
| GET | /alarms/firing | List alarms in ALARM state |
| POST | /agent/query | Natural language infrastructure query |

## Live Endpoint

```
https://api.samklin.online
https://api.samklin.online/health
```

---

## Toolkit

Reusable Boto3 classes for AWS automation. Import directly into any script or application.

```python
from toolkit import EC2Toolkit, S3Toolkit, IAMToolkit, MonitorToolkit

ec2 = EC2Toolkit(region="us-east-1")
ec2.list_instances()
ec2.list_running()
ec2.stop_instance("i-0abc123")
ec2.start_instance("i-0abc123")
ec2.get_instance_state("i-0abc123")

s3 = S3Toolkit(bucket_name="my-bucket", region="us-east-1")
s3.upload("report content", key="reports/report.txt")
s3.download("reports/report.txt")
s3.list_objects(prefix="reports/")
s3.delete("reports/report.txt")
s3.latest_object(prefix="reports/")

iam = IAMToolkit()
iam.list_users()
iam.list_roles()
iam.list_attached_policies("ecsTaskExecutionRole")
iam.get_user("devops-admin")

monitor = MonitorToolkit(region="us-east-1")
monitor.get_ec2_cpu("i-0abc123", minutes=10)
monitor.list_alarms()
monitor.alarms_in_alarm()
```

---

## CLI

```bash
# EC2
python cli.py ec2 list
python cli.py ec2 list --state running
python cli.py ec2 state i-0abc123
python cli.py ec2 stop i-0abc123
python cli.py ec2 start i-0abc123

# S3
python cli.py s3 list
python cli.py s3 list --prefix reports/
python cli.py s3 upload report.txt --key reports/report.txt
python cli.py s3 download reports/report.txt
python cli.py s3 delete reports/report.txt

# IAM
python cli.py iam users
python cli.py iam roles
python cli.py iam policies ecsTaskExecutionRole

# CloudWatch
python cli.py monitor alarms
python cli.py monitor alarms --state ALARM
python cli.py monitor firing
python cli.py monitor cpu i-0abc123
python cli.py monitor cpu i-0abc123 --minutes 30
```

---

## CI/CD Pipeline

Every push to `main` triggers:
1. pytest suite — 64 tests, 98% coverage
2. If tests pass → Docker build → ECR push → ECS force-redeploy
3. If tests fail → deployment blocked

Deploy job currently disabled — infrastructure torn down after Phase 1. Re-enabled in Phase 3.

---

## Test Suite

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=toolkit --cov=api --cov-report=term-missing
```

| File | Coverage |
|---|---|
| api.py | 95% |
| toolkit/ec2.py | 98% |
| toolkit/iam.py | 100% |
| toolkit/monitor.py | 100% |
| toolkit/s3.py | 100% |
| **Total** | **98%** |

---

## Observability

- **Dashboard:** CloudWatch — ECS CPU, Memory, ALB request count, 5xx errors
- **Alarms:** ECS CPU > 80%, Memory > 80%, ALB 5xx > 5/min
- **Alerting:** SNS topic → email

---

## Infrastructure

- **ECS Cluster:** pyops-cluster
- **ECS Service:** pyops-api-svc (Fargate, 256 CPU / 512 MB)
- **ECR Repository:** pyops-api
- **ALB:** pyops-api-alb (internet-facing)
- **Target Group:** pyops-api-tg (health check on /health)
- **Certificate:** ACM — api.samklin.online
- **CloudWatch Dashboard:** pyops-dashboard

---

## Phase Roadmap

| Phase | Focus | Status |
|---|---|---|
| Phase 1 (Weeks 1–4) | ECS deployment, CI/CD, ALB, observability | ✅ Complete |
| Phase 2 (Weeks 5–8) | Boto3 toolkit, FastAPI testing, CLI | ✅ Complete |
| Phase 3 (Weeks 9–12) | LLMs, RAG pipelines, AI ops agent on Kubernetes | 🔜 Next |
