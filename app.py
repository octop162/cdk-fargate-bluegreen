import aws_cdk as cdk

from network.network_stack import NetworkStack
from container.container_stack import ContainerStack
from container.container_sub_stack import ContainerSubStack
from container.repository_stack import RepositoryStack
from settings.constant import Constant


app = cdk.App()
network_stack = NetworkStack(
    app,
    "network-stack",
    env=Constant.ACCOUNT_ENV)

repository_stack = RepositoryStack(
    app,
    "repository-stack",
    env=Constant.ACCOUNT_ENV)

container_stack = ContainerStack(
    app, "container-stack",
    env=Constant.ACCOUNT_ENV
)

container_stack = ContainerSubStack(
    app, "container-sub-stack",
    env=Constant.ACCOUNT_ENV
)

app.synth()
