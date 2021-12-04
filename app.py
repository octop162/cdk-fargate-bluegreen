import aws_cdk as cdk

from network.network_stack import NetworkStack
from app.app_stack import AppStack


app = cdk.App()
NetworkStack(app, "network-stack")

app.synth()
