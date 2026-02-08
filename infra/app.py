#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.infra_stack import InfraStack


app = cdk.App()
myInfraStack_dev = InfraStack(app, "InfraStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

# --- ここでタグを一括設定 ---
owner = os.getenv("OWNER_NAME_01", "default_user")
cdk.Tags.of(myInfraStack_dev).add("Project", "photolog")
cdk.Tags.of(myInfraStack_dev).add("Owner", owner)
cdk.Tags.of(myInfraStack_dev).add("Environment", "dev")

app.synth()
