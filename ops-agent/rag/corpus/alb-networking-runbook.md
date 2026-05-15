# ALB Networking Runbook

## Architecture
internet → api.samklin.online (Route53)
→ ACM Certificate (HTTPS/443)
→ Application Load Balancer
→ Target Group (health check: /health)
→ ECS Tasks / EKS Pods

## Health Check Configuration
- Protocol: HTTP
- Path: /health
- Healthy threshold: 2
- Unhealthy threshold: 3
- Timeout: 5s
- Interval: 30s

## 502 Bad Gateway
Symptoms: ALB returns 502, targets show unhealthy.
Probable causes: application not listening on expected port, health check path returning non-200, ECS task crashed before registering with target group.

Remediation steps:
1. ALB Console → Target Groups → check target health status
2. Verify health check path /health returns HTTP 200
3. Check security group allows ALB to ECS/EKS traffic on app port
4. Review ECS task logs for startup errors

## 504 Gateway Timeout
Symptoms: Requests timing out at ALB layer.
Probable causes: application response time exceeds ALB idle timeout (default 60s), database query hanging, downstream API not responding.

Remediation steps:
1. Check ALB access logs for request duration
2. Review CloudWatch TargetResponseTime metric
3. Increase ALB idle timeout if legitimate long-running requests
4. Implement request timeout in application layer

## SSL Certificate Issues
Symptoms: HTTPS failing, certificate warnings.
Remediation steps:
1. ACM Console — verify certificate status is Issued
2. Confirm certificate covers api.samklin.online domain
3. Check ALB listener on port 443 references correct certificate ARN
4. Verify Route53 A record points to correct ALB DNS name