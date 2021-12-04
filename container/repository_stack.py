from constructs import Construct
from aws_cdk import (
    Stack,
    aws_ecr as ecr,
)


class RepositoryStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ECR作成
        ecr_repo = ecr.Repository(self, "AppRepository")

        self.ecr_repo = ecr_repo