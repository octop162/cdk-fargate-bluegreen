#!/usr/bin/env python3

import aws_cdk as cdk

from cdk_fargate_bluegreen.cdk_fargate_bluegreen_stack import CdkFargateBluegreenStack


app = cdk.App()
CdkFargateBluegreenStack(app, "cdk-fargate-bluegreen")

app.synth()
