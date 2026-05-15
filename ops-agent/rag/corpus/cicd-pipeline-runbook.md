# CI/CD Pipeline Runbook

## Pipeline Overview
git push to main triggers GitHub Actions.
GitHub Actions runs pytest gate, then builds Docker image, pushes to Amazon ECR, and deploys to EKS cluster.

## pytest Gate Failing
Symptoms: GitHub Actions workflow fails at test step.
Remediation steps:
1. Check Actions tab in GitHub for failed step output
2. Run tests locally: pytest tests/ -v
3. Check for missing environment variables in GitHub Secrets
4. Verify test dependencies installed: pip install -r requirements-dev.txt
5. Check if tests are environment-specific with missing mocks

## ECR Push Failing
Symptoms: Docker push step fails in GitHub Actions.
Probable causes: IAM role or OIDC misconfigured, GitHub Actions lacks ECR push permission, ECR repository does not exist, image tag conflict.

Remediation steps:
1. Verify GitHub OIDC role has ecr:GetAuthorizationToken and ecr:PutImage permissions
2. Confirm ECR repo exists: aws ecr describe-repositories
3. Check workflow IAM role ARN matches trust policy
4. Re-run workflow after fixing permissions

## Deployment Not Triggering
Symptoms: ECR push succeeds but EKS not updated.
Remediation steps:
1. Check GitHub Actions deploy step logs
2. Verify AWS credentials and role in GitHub Secrets are current
3. Confirm EKS cluster name matches workflow config
4. Verify kubeconfig and kubectl version compatibility

## Key Environment Variables Required
- AWS_REGION: target deployment region
- ECR_REGISTRY: ECR registry URL
- ECR_REPOSITORY: repository name
- EKS_CLUSTER: target cluster name
- ANTHROPIC_API_KEY: for opsAgent stored in GitHub Secrets and Kubernetes Secret