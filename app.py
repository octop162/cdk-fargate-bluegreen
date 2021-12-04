import aws_cdk as cdk

from network.network_stack import NetworkStack
from container.container_stack import ContainerStack
from container.repository_stack import RepositoryStack


app = cdk.App()
network_stack = NetworkStack(app, "network-stack")
repository_stack = RepositoryStack(app, "repository-stack")
container_stack = ContainerStack(
    app, "container-stack",
    vpc=network_stack.vpc,
    ecr_repo=repository_stack.ecr_repo
)

app.synth()
