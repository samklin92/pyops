import boto3
import logging

logger = logging.getLogger(__name__)


class IAMToolkit:

    def __init__(self):
        self.client = boto3.client("iam")

    def list_users(self):
        """List all IAM users in the account."""
        response = self.client.list_users()
        users = [
            {
                "username": u["UserName"],
                "user_id": u["UserId"],
                "created": u["CreateDate"].isoformat(),
                "arn": u["Arn"]
            }
            for u in response["Users"]
        ]
        logger.info(f"Found {len(users)} IAM users")
        return users

    def list_roles(self):
        """List all IAM roles in the account."""
        response = self.client.list_roles()
        roles = [
            {
                "name": r["RoleName"],
                "role_id": r["RoleId"],
                "created": r["CreateDate"].isoformat(),
                "arn": r["Arn"]
            }
            for r in response["Roles"]
        ]
        logger.info(f"Found {len(roles)} IAM roles")
        return roles

    def list_attached_policies(self, role_name):
        """List policies attached to a specific role."""
        response = self.client.list_attached_role_policies(RoleName=role_name)
        policies = [
            {
                "name": p["PolicyName"],
                "arn": p["PolicyArn"]
            }
            for p in response["AttachedPolicies"]
        ]
        logger.info(f"Found {len(policies)} policies on role {role_name}")
        return policies

    def get_user(self, username):
        """Get details for a specific IAM user."""
        try:
            response = self.client.get_user(UserName=username)
            u = response["User"]
            return {
                "username": u["UserName"],
                "user_id": u["UserId"],
                "created": u["CreateDate"].isoformat(),
                "arn": u["Arn"]
            }
        except Exception as e:
            logger.error(f"Failed to get user {username}: {e}")
            raise