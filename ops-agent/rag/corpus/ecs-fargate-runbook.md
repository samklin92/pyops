# ECS Fargate Runbook

## Service Overview
- Platform: AWS ECS Fargate
- Registry: Amazon ECR
- Deployment: GitHub Actions CI/CD pipeline
- Endpoint: api.samklin.online (HTTPS)

## Common Alerts and Remediation

### High Error Rate (5xx)
**Symptoms:** CloudWatch alarm on HTTPCode_Target_5XX_Count  
**Probable causes:**
- Application crash — check ECS task logs in CloudWatch
- Memory limit exceeded — task OOM killed, increase task memory
- Dependency failure — downstream service or database unreachable

**Remediation steps:**
1. Check ECS task logs: CloudWatch > Log Groups > /ecs/your-service
2. Check task stopped reason: ECS Console > Tasks > Stopped
3. Verify ECR image pulled successfully
4. Roll back to previous task definition if recent deployment
5. Scale out desired count if load-related

### Task Keeps Restarting
**Symptoms:** ECS task exit code non-zero, rapid restart loop  
**Probable causes:**
- Missing environment variable or secret
- Health check failing — ALB deregistering tasks immediately
- Application startup crash

**Remediation steps:**
1. ECS Console > Service > Events tab for stop reasons
2. Verify all SSM/Secrets Manager references are valid
3. Check health check path returns 200 on /health endpoint
4. Review task definition environment variables

### Deployment Stuck / Rollback
**Symptoms:** New deployment not completing, old tasks not draining  
**Remediation steps:**
1. ECS Console > Service > Deployments tab
2. Force new deployment if stuck: `aws ecs update-service --force-new-deployment`
3. Check ALB target group — ensure new tasks pass health checks
4. Rollback: update service to previous task definition revision

## Key Metrics to Monitor
- CPUUtilization > 80% → scale out
- MemoryUtilization > 85% → increase task memory or scale out
- HTTPCode_Target_5XX_Count > 10/min → investigate immediately
- TargetResponseTime > 2s → check downstream dependencies