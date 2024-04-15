/**********************************************************************************************************************
 *  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.                                                *
 *                                                                                                                    *
 *  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance    *
 *  with the License. A copy of the License is located at                                                             *
 *                                                                                                                    *
 *      http://www.apache.org/licenses/LICENSE-2.0                                                                    *
 *                                                                                                                    *
 *  or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES *
 *  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    *
 *  and limitations under the License.                                                                                *
 *********************************************************************************************************************/

import { App, CfnOutput, Stack, StackProps } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as dotenv from "dotenv";
import * as path from "path";

import { LLMApiStack } from "../lib/api/api-stack";
import { ConnectorStack } from "../lib/connector/connector-stack";
import { DynamoDBConstruct } from "../lib/db/dynamodb";
import { EtlStack } from "../lib/etl/etl-stack";
import { AssetsStack } from "../lib/model/assets-stack";
import { LLMStack } from "../lib/model/llm-stack";
import { BuildConfig } from "../lib/shared/build-config";
import { DeploymentParameters } from "../lib/shared/cdk-parameters";
import { VpcConstruct } from "../lib/shared/vpc-stack";
import { OpenSearchStack } from "../lib/vector-store/os-stack";
import { PortalConstruct } from "../lib/ui/ui-portal";

dotenv.config();

export class RootStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps = {}) {
    super(scope, id, props);

    this.setBuildConfig();

    const cdkParameters = new DeploymentParameters(this);

    const assetsStack = new AssetsStack(this, "assets-stack", {
      s3ModelAssets: cdkParameters.s3ModelAssets.valueAsString,
      env: process.env,
    });
    const llmStack = new LLMStack(this, "llm-stack", {
      s3ModelAssets: cdkParameters.s3ModelAssets.valueAsString,
      rerankModelPrefix: assetsStack.rerankModelPrefix,
      rerankModelVersion: assetsStack.rerankModelVersion,
      embeddingModelPrefix: assetsStack.embeddingModelPrefix,
      embeddingModelVersion: assetsStack.embeddingModelVersion,
      instructModelPrefix: assetsStack.instructModelPrefix,
      instructModelVersion: assetsStack.instructModelVersion,
      env: process.env,
    });
    llmStack.addDependency(assetsStack);

    const vpcConstruct = new VpcConstruct(this, "vpc-construct");

    const osStack = new OpenSearchStack(this, "os-stack", {
      osVpc: vpcConstruct.connectorVpc,
      securityGroup: vpcConstruct.securityGroup,
    });
    osStack.node.addDependency(vpcConstruct);

    const dynamoDBConstruct = new DynamoDBConstruct(this, "ddb-construct");

    const etlStack = new EtlStack(this, "etl-stack", {
      domainEndpoint: osStack.domainEndpoint || "",
      embeddingEndpoint: llmStack.embeddingEndPoints,
      region: props.env?.region || "us-east-1",
      subEmail: cdkParameters.subEmail.valueAsString ?? "",
      etlVpc: vpcConstruct.connectorVpc,
      subnets: vpcConstruct.privateSubnets,
      securityGroups: vpcConstruct.securityGroup,
      s3ModelAssets: cdkParameters.s3ModelAssets.valueAsString,
      openSearchIndex: cdkParameters.openSearchIndex.valueAsString,
      imageName: cdkParameters.etlImageName.valueAsString,
      etlTag: cdkParameters.etlImageTag.valueAsString,
    });
    etlStack.node.addDependency(vpcConstruct);
    etlStack.addDependency(osStack);
    etlStack.addDependency(llmStack);

    const connectorStack = new ConnectorStack(this, "connector-stack", {
      connectorVpc: vpcConstruct.connectorVpc,
      securityGroup: vpcConstruct.securityGroup,
      domainEndpoint: osStack.domainEndpoint || "",
      embeddingEndPoints: llmStack.embeddingEndPoints,
      openSearchIndex: cdkParameters.openSearchIndex.valueAsString,
      openSearchIndexDict: cdkParameters.openSearchIndexDict.valueAsString,
      env: process.env,
    });
    connectorStack.node.addDependency(vpcConstruct);
    connectorStack.addDependency(osStack);
    connectorStack.addDependency(llmStack);

    const apiStack = new LLMApiStack(this, "api-stack", {
      apiVpc: vpcConstruct.connectorVpc,
      securityGroup: vpcConstruct.securityGroup,
      domainEndpoint: osStack.domainEndpoint || "",
      rerankEndPoint: llmStack.rerankEndPoint ?? "",
      embeddingEndPoints: llmStack.embeddingEndPoints || "",
      llmModelId: BuildConfig.LLM_MODEL_ID,
      instructEndPoint:
        BuildConfig.LLM_ENDPOINT_NAME !== ""
          ? BuildConfig.LLM_ENDPOINT_NAME
          : llmStack.instructEndPoint,
      sessionsTableName: dynamoDBConstruct.sessionTableName,
      messagesTableName: dynamoDBConstruct.messageTableName,
      workspaceTableName: etlStack.workspaceTableName,
      sfnOutput: etlStack.sfnOutput,
      openSearchIndex: cdkParameters.openSearchIndex.valueAsString,
      openSearchIndexDict: cdkParameters.openSearchIndexDict.valueAsString,
      jobName: connectorStack.jobName,
      jobQueueArn: connectorStack.jobQueueArn,
      jobDefinitionArn: connectorStack.jobDefinitionArn,
      etlEndpoint: etlStack.etlEndpoint,
      resBucketName: etlStack.resBucketName,
      executionTableName: etlStack.executionTableName,
      env: process.env,
    });
    apiStack.node.addDependency(vpcConstruct);
    apiStack.addDependency(osStack);
    apiStack.addDependency(llmStack);
    apiStack.addDependency(connectorStack);
    apiStack.addDependency(etlStack);

    const uiPortal = new PortalConstruct(this, "ui-construct", {
      websocket: apiStack.wsEndpoint,
      apiUrl: apiStack.apiEndpoint,
    });

    uiPortal.node.addDependency(apiStack);

    new CfnOutput(this, "API Endpoint Address", {
      value: apiStack.apiEndpoint,
    });
    new CfnOutput(this, "AOS Index Dict", {
      value: cdkParameters.openSearchIndexDict.valueAsString,
    });
    new CfnOutput(this, "Chunk Bucket", { value: etlStack.resBucketName });
    new CfnOutput(this, "Cross Model Endpoint", {
      value: llmStack.rerankEndPoint || "No Cross Endpoint Created",
    });
    new CfnOutput(this, "Document Bucket", { value: apiStack.documentBucket });
    new CfnOutput(this, "Embedding Model Endpoint", {
      value: llmStack.embeddingEndPoints[0] || "No Embedding Endpoint Created",
    });
    new CfnOutput(this, "Glue Job Name", { value: etlStack.jobName });
    new CfnOutput(this, "Instruct Model Endpoint", {
      value: llmStack.instructEndPoint || "No Instruct Endpoint Created",
    });
    new CfnOutput(this, "OpenSearch Endpoint", {
      value: osStack.domainEndpoint || "No OpenSearch Endpoint Created",
    });
    new CfnOutput(this, "Processed Object Table", {
      value: etlStack.executionTableName,
    });
    new CfnOutput(this, "VPC", { value: vpcConstruct.connectorVpc.vpcId });
    new CfnOutput(this, "WebPortalURL", {
      value: uiPortal.portalUrl,
      description: "LLM-Bot web portal url",
    });
    new CfnOutput(this, "WebSocket Endpoint Address", {
      value: apiStack.wsEndpoint,
    });
  }

  private setBuildConfig() {
    BuildConfig.DEPLOYMENT_MODE =
      this.node.tryGetContext("DeploymentMode") ?? "ALL";
    BuildConfig.LAYER_PIP_OPTION =
      this.node.tryGetContext("LayerPipOption") ?? "";
    BuildConfig.JOB_PIP_OPTION = this.node.tryGetContext("JobPipOption") ?? "";
    BuildConfig.LLM_MODEL_ID =
      this.node.tryGetContext("LlmModelId") ?? "internlm2-chat-7b";
    BuildConfig.LLM_ENDPOINT_NAME =
      this.node.tryGetContext("LlmEndpointName") ?? "";
  }
}

// For development, use account/region from CDK CLI
const devEnv = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION,
};

const app = new App();
new RootStack(app, "llm-bot-dev", { env: devEnv });
app.synth();
