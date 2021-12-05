from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_iam as iam,
)
from settings.constant import Constant

class ContainerSubStack(Stack):

    def __init__(
            self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        '''
        IAMRole
        '''
        bluegreen_deployment_service_role = iam.Role(
            self,
            'BlueGreenDeploymentRole',
            role_name=Constant.IAM_BLUEGREEN_DEPLOYMENT_SERVICE_ROLE_NAME,
            assumed_by= iam.ServicePrincipal("codedeploy.amazonaws.com"),
            description='blue green deployment role',
        )
        bluegreen_deployment_service_role.add_to_policy(
            iam.PolicyStatement(
                resources=['*'],
                actions=[
                    'codedeploy:Get*',
                    'codedeploy:CreateCloudFormationDeployment',
                    'iam:PassRole',
                ]
            )
        )
        # bluegreen_deployment_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name('arn:aws:iam::aws:policy/AWSCodeDeployRoleForECS')
        # )

        CfnOutput(
            self,
            'BlueGreenDeploymentServiceRoleName',
            value=bluegreen_deployment_service_role.role_name
        )
