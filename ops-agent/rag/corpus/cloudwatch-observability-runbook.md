# CloudWatch Observability Runbook

## Observability Stack
ECS Tasks and EKS Pods send logs to CloudWatch Logs.
CloudWatch Metrics collect infrastructure and custom metrics.
CloudWatch Alarms trigger on thresholds and notify via SNS Topic.
SNS delivers to email and opsAgent webhook.

## Alarm Inventory
- HighErrorRate: HTTPCode_Target_5XX_Count greater than 10 per minute → SNS to opsAgent
- HighLatency: TargetResponseTime greater than 2s average → SNS to opsAgent
- HighCPU: CPUUtilization greater than 80 percent → SNS to email
- HighMemory: MemoryUtilization greater than 85 percent → SNS to email
- UnhealthyHosts: UnHealthyHostCount greater than 0 → SNS to opsAgent

## Alarm Firing but No Notification
Symptoms: Alarm state is ALARM in console but no email or webhook received.
Remediation steps:
1. SNS Console → Topic → check subscriptions are confirmed
2. Verify email subscription confirmed, check spam folder
3. Check SNS topic ARN matches alarm action ARN
4. Test SNS manually: aws sns publish --topic-arn ARN --message test

## Missing Logs
Symptoms: ECS tasks running but no logs appearing in CloudWatch.
Remediation steps:
1. Verify task definition log configuration points to correct log group
2. Check ECS task IAM role has logs:PutLogEvents permission
3. Confirm log group exists: aws logs describe-log-groups
4. Check awslogs driver configured in task definition

## Dashboard Not Updating
Symptoms: CloudWatch dashboard showing stale or missing data.
Remediation steps:
1. Verify metric namespace and dimensions match exactly
2. Check time range is set correctly
3. Confirm metrics are being published by the service
4. Use Metrics Insights query to verify data exists

## Useful Log Query Patterns
Filter all errors in last hour: fields timestamp and message, filter message like ERROR, sort timestamp desc, limit 50.
Count 5xx errors by path: fields timestamp status path, filter status >= 500, stats count by path, sort count desc.