# High CPU Utilization Runbook

## Trigger
CPU utilization exceeds 75% for more than 5 minutes.

## Immediate Actions
1. Check running processes: `top` or `htop`
2. Identify the top CPU-consuming process
3. Check application logs for errors or loops
4. Review CloudWatch metrics for the last 1 hour

## Escalation
- CPU > 85% for 10 minutes: scale up instance type
- CPU > 95% for 5 minutes: immediately terminate and replace instance
- Notify on-call engineer if not resolved in 15 minutes

## Prevention
- Set CloudWatch alarm at 75% CPU threshold
- Implement auto-scaling policies
- Review instance sizing monthly