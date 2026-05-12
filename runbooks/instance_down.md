# Instance Down Runbook

## Trigger
EC2 instance state changes to stopped or terminated unexpectedly.

## Immediate Actions
1. Check instance status in AWS Console or via CLI
2. Review system logs: `aws ec2 get-console-output`
3. Check for scheduled maintenance events
4. Verify security group and network ACL rules

## Recovery Steps
1. Attempt to start the instance: `aws ec2 start-instances`
2. If start fails, launch a replacement from AMI snapshot
3. Update DNS or load balancer to point to new instance
4. Restore data from latest snapshot if needed

## Escalation
- Instance down for more than 5 minutes: page on-call engineer
- Data loss suspected: escalate to incident commander immediately