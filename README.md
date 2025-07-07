# Chat PDF GraphRAG with Langchain + Neo4j + Bedrock

This repository contains a Graph RAG (Retrieval-Augmented Generation) application that uses PDF documents as a knowledge source, with Neo4j as the graph database and AWS Bedrock for AI model access.

## Infrastructure as Code

The repository provides two options for deploying the AWS infrastructure required by the application:

1. **Terraform** (in the root directory)
2. **AWS CDK with Python** (in the `cdk` directory)

Both options create the same AWS resources and provide equivalent functionality. You can choose the option that best fits your workflow and preferences.

### Infrastructure Components

The infrastructure includes the following AWS resources:

- **S3 Bucket**: For storing PDF and text documents
- **SQS Queue**: For Celery task queue
- **IAM Role**: For EC2 instances or other AWS services to access the resources
- **IAM User**: For programmatic access to AWS resources
- **IAM Policies**: For S3, SQS, Bedrock, and Textract access
- **AWS Bedrock**: For AI model access and logging configuration
- **CloudWatch Log Group**: For Bedrock invocation logging

### Terraform vs CDK

#### Terraform

Terraform is a popular infrastructure as code tool that uses a declarative language (HCL) to define resources. The Terraform configuration in this repository:

- Uses official AWS modules from the Terraform Registry
- Organizes resources into separate files by type
- Uses variables and outputs for configuration and information sharing
- Provides a comprehensive README with usage instructions

For more information, see [terraform-README.md](terraform-README.md).

#### AWS CDK

AWS CDK (Cloud Development Kit) allows you to define infrastructure using familiar programming languages. The CDK configuration in this repository:

- Uses Python to define AWS resources
- Organizes resources into separate stack classes
- Uses environment variables for configuration
- Provides a comprehensive README with usage instructions

For more information, see [cdk/README.md](cdk/README.md).

### Getting Started

To get started with either option, refer to the respective README files:

- [Terraform README](terraform-README.md)
- [CDK README](cdk/README.md)

## Application Components

- **Neo4j**: Graph database for storing document knowledge graphs
- **Langchain**: Framework for building applications with LLMs
- **AWS Bedrock**: Managed service for foundation models
- **Celery**: Distributed task queue for processing documents
- **SQS**: Message broker for Celery tasks
- **S3**: Storage for PDF and text documents

## Notes

- The Neo4j database is not deployed by either Terraform or CDK. Instead, it's configured to run in Docker as shown in the `docker-compose.yaml` file.
- Both infrastructure configurations create an IAM user with permissions to access S3, SQS, Bedrock, and Textract. You may want to restrict these permissions further in a production environment.
