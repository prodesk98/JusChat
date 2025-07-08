# JusChat - Assistente Jurídico com GraphRAG

JusChat é um assistente jurídico inteligente baseado em tecnologia GraphRAG (Graph Retrieval Augmented Generation) que utiliza processamento de linguagem natural e grafos de conhecimento para consulta e análise de documentos jurídicos brasileiros.

## 📋 Sobre o Projeto

JusChat foi desenvolvido para auxiliar profissionais do direito e interessados na área jurídica a consultar e analisar documentos legais de forma eficiente. O sistema utiliza uma abordagem avançada de RAG (Retrieval Augmented Generation) combinada com banco de dados em grafo para criar uma representação estruturada do conhecimento jurídico, permitindo consultas mais precisas e contextualizadas.

O assistente é capaz de:
- Processar documentos jurídicos (PDFs, TXTs, MDs)
- Extrair entidades e relações jurídicas
- Armazenar conhecimento em um grafo semântico
- Responder perguntas complexas sobre processos e conceitos jurídicos
- Fornecer respostas fundamentadas com base nos documentos analisados

## 🛠️ Stack Tecnológica

### Backend
- **FastAPI**: Framework web para APIs
- **LangChain**: Framework para aplicações baseadas em LLMs
- **LangGraph**: Orquestração de fluxos de trabalho para agentes de IA
- **Neo4j**: Banco de dados em grafo para armazenamento de conhecimento
- **MongoDB**: Banco de dados para armazenamento de histórico de conversas
- **Amazon Bedrock**: Serviço de LLM (Claude 3.5 Sonnet)
- **Amazon S3**: Armazenamento de documentos
- **Amazon SQS**: Fila de mensagens para processamento assíncrono
- **Amazon Textract**: Extração de texto de documentos PDF

### Frontend
- **Jinja2**: Engine de templates
- **TailwindCSS**: Framework CSS para estilização
- **JavaScript**: Interatividade no frontend

## ✨ Funcionalidades

- **Upload de Documentos**: Carregue documentos jurídicos (PDF, TXT, MD) para alimentar a base de conhecimento
- **Extração de Conhecimento**: Processamento automático de documentos para extrair entidades e relações jurídicas
- **Consulta Conversacional**: Interface de chat para realizar perguntas sobre documentos jurídicos
- **Busca Semântica**: Recuperação de informações baseada em significado, não apenas em palavras-chave
- **Raciocínio em Grafo**: Utilização da estrutura de grafo para realizar inferências complexas
- **Geração de Respostas Contextualizadas**: Respostas geradas com base no contexto jurídico brasileiro

## 🧠 Arquitetura do GraphRAG

O JusChat utiliza uma arquitetura GraphRAG que combina:

1. **Ingestão de Documentos**: Processamento e divisão de documentos em chunks
2. **Extração de Conhecimento**: Identificação de entidades jurídicas (pessoas, organizações, tribunais, etc.) e suas relações
3. **Armazenamento em Grafo**: Persistência do conhecimento em um banco de dados Neo4j
4. **Consulta e Raciocínio**: Workflow de busca, roteamento, geração de subconsultas e resposta final
5. **Geração Aumentada**: Uso do LLM (Claude 3.5) para gerar respostas precisas com base no conhecimento recuperado

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

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.10+
- Docker e Docker Compose (para Neo4j e MongoDB)
- Conta AWS com acesso aos serviços Bedrock, S3, SQS e Textract

### Configuração do Ambiente

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/juschat.git
cd juschat
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -e .
```

4. Configure as variáveis de ambiente:
Copie o arquivo `template.env` para `.env` e preencha com suas credenciais:
```bash
cp template.env .env
```

5. Inicie os serviços com Docker Compose:
```bash
docker-compose up -d
```

## 🔧 Uso

1. Inicie o servidor:
```bash
python main.py
```

2. Acesse a interface web em `http://localhost:8000`

3. Faça upload de documentos jurídicos para alimentar a base de conhecimento

4. Comece a fazer perguntas sobre os documentos carregados

## 🧪 Testes

O JusChat inclui testes unitários para garantir a qualidade e a estabilidade do código. Os testes são focados principalmente nas APIs FastAPI.

### Executando os Testes

Para executar os testes localmente:

```bash
# Instale as dependências de desenvolvimento
pip install -r requirements-dev.txt

# Execute os testes
pytest tests/
```

Para executar os testes com cobertura:

```bash
pytest tests/ --cov=. --cov-report=term
```

### Estrutura de Testes

- `tests/conftest.py`: Configuração e fixtures do pytest
- `tests/test_api.py`: Testes para os endpoints da API FastAPI

## 🔄 CI/CD

O projeto utiliza GitHub Actions para integração contínua e entrega contínua. Os workflows estão configurados para:

1. **Testes Automatizados**: Executa os testes unitários em cada push e pull request
2. **Análise de Código**: Verifica a qualidade do código com linters como flake8, black e isort
3. **Relatórios de Cobertura**: Gera relatórios de cobertura de código

Os workflows estão definidos em `.github/workflows/python-tests.yml`.

## ⚠️ Notas

- O banco de dados Neo4j não é implantado pelo Terraform ou CDK. Em vez disso, ele é configurado para ser executado no Docker, conforme mostrado no arquivo `docker-compose.yaml`.
- Ambas as configurações de infraestrutura criam um usuário IAM com permissões para acessar S3, SQS, Bedrock e Textract. Você pode querer restringir ainda mais essas permissões em um ambiente de produção.
- Este sistema não substitui o aconselhamento jurídico profissional. As respostas geradas devem ser verificadas por profissionais qualificados.

## 📄 Licença

Este projeto está licenciado sob Creative Commons - veja o arquivo LICENSE para mais detalhes.
