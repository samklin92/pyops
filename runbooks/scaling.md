# Scaling Runbook

## When to Scale Up
- CPU consistently above 80% for 15 minutes
- Memory utilization above 85%
- Response time degradation detected

## Vertical Scaling (Instance Resize)
1. Create AMI snapshot of current instance
2. Stop the instance
3. Change instance type via AWS Console or CLI
4. Start the instance
5. Verify application health

## Horizontal Scaling (Add Instances)
1. Launch new instance from same AMI
2. Configure same security groups and IAM role
3. Register with load balancer target group
4. Verify health checks pass
5. Monitor for 10 minutes before considering stable

## Auto Scaling
- Minimum instances: 2 (for high availability)
- Maximum instances: 10
- Scale out policy: CPU > 75% for 3 minutes
- Scale in policy: CPU < 30% for 10 minutes