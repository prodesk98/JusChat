from typing import Optional

from langchain_community.document_loaders import S3FileLoader, AmazonTextractPDFLoader
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_experimental.graph_transformers.llm import UnstructuredRelation
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
from langchain_aws import ChatBedrock
from langchain_neo4j import Neo4jGraph

from config import env


examples = [
    {
        "text": (
            "Maria Silva é autora em um processo contra a Empresa XYZ "
            "no Tribunal de Justiça de São Paulo."
        ),
        "head": "Maria Silva",
        "head_type": "Person",
        "relation": "PARTY_TO",
        "tail": "Processo 1020304-55.2023.8.26.0100",
        "tail_type": "Legal_Case",
    },
    {
        "text": (
            "A Empresa XYZ foi representada pelo escritório de advocacia Souza & Associados."
        ),
        "head": "Souza & Associados",
        "head_type": "Organization",
        "relation": "REPRESENTS",
        "tail": "Empresa XYZ",
        "tail_type": "Organization",
    },
    {
        "text": (
            "O processo está sendo julgado pelo Tribunal de Justiça de São Paulo."
        ),
        "head": "Processo 1020304-55.2023.8.26.0100",
        "head_type": "Legal_Case",
        "relation": "HANDLED_BY",
        "tail": "Tribunal de Justiça de São Paulo",
        "tail_type": "Court",
    },
    {
        "text": (
            "O Tribunal de Justiça de São Paulo está localizado na cidade de São Paulo."
        ),
        "head": "Tribunal de Justiça de São Paulo",
        "head_type": "Court",
        "relation": "LOCATED_IN",
        "tail": "São Paulo",
        "tail_type": "Location",
    },
    {
        "text": (
            "A petição inicial do processo faz referência ao Artigo 927 do Código Civil."
        ),
        "head": "Petição Inicial",
        "head_type": "Legal_Document",
        "relation": "REFERS_TO",
        "tail": "Artigo 927",
        "tail_type": "Law_Article",
    },
    {
        "text": (
            "A decisão judicial resultou em condenação por danos morais."
        ),
        "head": "Decisão Judicial",
        "head_type": "Legal_Document",
        "relation": "RESULTS_IN",
        "tail": "Danos Morais",
        "tail_type": "Penalty",
    },
    {
        "text": (
            "Foi interposto recurso de apelação pela Empresa XYZ."
        ),
        "head": "Processo 1020304-55.2023.8.26.0100",
        "head_type": "Legal_Case",
        "relation": "HAS_ACTION",
        "tail": "Apelação 2030405-66.2023.8.26.0100",
        "tail_type": "Appeal",
    },
    {
        "text": (
            "A audiência de instrução ocorreu no Fórum João Mendes."
        ),
        "head": "Audiência de Instrução",
        "head_type": "Event",
        "relation": "HELD_ON",
        "tail": "Fórum João Mendes",
        "tail_type": "Location",
    },
    {
        "text": (
            "O laudo pericial foi incluído como prova no processo."
        ),
        "head": "Laudo Pericial",
        "head_type": "Evidence",
        "relation": "EVIDENCE_IN",
        "tail": "Processo 1020304-55.2023.8.26.0100",
        "tail_type": "Legal_Case",
    },
    {
        "text": (
            "O juiz Pedro Almeida decidiu o processo em favor de Maria Silva."
        ),
        "head": "Pedro Almeida",
        "head_type": "Person",
        "relation": "DECIDED_BY",
        "tail": "Processo 1020304-55.2023.8.26.0100",
        "tail_type": "Legal_Case",
    },
]

nodes = [
    "Person",
    "Organization",
    "Court",
    "Legal_Case",
    "Legal_Action",
    "Legal_Document",
    "Law",
    "Law_Article",
    "Legal_Concept",
    "Evidence",
    "Event",
    "Location",
    "Contract",
    "Penalty",
    "Appeal",
]

relationships = [
    "PARTY_TO",
    "REPRESENTS",
    "EMPLOYED_BY",
    "HANDLED_BY",
    "LOCATED_IN",
    "REFERS_TO",
    "EVIDENCE_IN",
    "DOCUMENT_OF",
    "HAS_ACTION",
    "HELD_ON",
    "RELATED_TO",
    "DECIDED_BY",
    "APPEALED_TO",
    "RESULTS_IN",
    "CITES",
]

class KnowledgeService:
    def __init__(self):
        self._splitter = CharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=300,
            chunk_overlap=50,
        )

    @staticmethod
    def _create_unstructured_prompt(
        node_labels: Optional[list[str]] = None,
        rel_types: Optional[list[str] | list[tuple[str, str, str]]] = None,
        relationship_type: Optional[str] = None,
        additional_instructions: Optional[str] = "",
    ) -> ChatPromptTemplate:
        node_labels_str = str(node_labels) if node_labels else ""
        if rel_types:
            if relationship_type == "tuple":
                rel_types_str = str(list({item[1] for item in rel_types}))
            else:
                rel_types_str = str(rel_types)
        else:
            rel_types_str = ""

        base_string_parts = [
            "You are a legal extraction assistant specialized in the Brazilian legal domain. "
            "Your task is to extract structured legal information from text in order to build "
            "a Brazilian legal knowledge graph. Identify legal entities and their relations "
            "strictly following the user prompt. You must produce output in JSON format, "
            "containing a list of JSON objects. Each object must have the keys: \"head\", "
            "\"head_type\", \"relation\", \"tail\", and \"tail_type\". The \"head\" key must "
            "contain the extracted entity text, which must match one of the allowed entity types "
            f"from {node_labels_str}." if node_labels else "",
            f"The \"head_type\" key must contain the type of the head entity, "
            f"limited to the allowed types: {node_labels_str}." if node_labels else "",
            f"The \"relation\" key must contain the relation type linking \"head\" and \"tail\", "
            f"which must be one of: {rel_types_str}." if rel_types else "",
            f"The \"tail\" key must contain the text of the related entity, "
            f"and the \"tail_type\" key must contain its type, again limited to: {node_labels_str}."
            if node_labels else "",
            "Extract only legal relations that match the allowed schema. "
            "Relations can only occur between specific entity types according to the schema "
            "in the format: (EntityType1, RELATION_TYPE, EntityType2).\n"
            f"The defined schema is: {rel_types}" if relationship_type == "tuple" else "",
            "Extract as many relevant legal entities and relations as possible. "
            "Maintain entity consistency: if an entity, like \"Maria Silva\", appears "
            "multiple times under different names or pronouns, always use the most complete "
            "identifier. The knowledge graph must remain coherent and easy to interpret.",
            "IMPORTANT:\n- Do not add any explanation or extra text. Output JSON only.\n",
            additional_instructions,
        ]
        system_prompt = "\n".join(filter(None, base_string_parts))

        system_message = SystemMessage(content=system_prompt)
        parser = JsonOutputParser(pydantic_object=UnstructuredRelation)

        human_string_parts = [
            "Based on the example below, extract legal entities and "
            "relations from the provided text.\n\n",
            "Use only the following allowed entity types:\n# ENTITY TYPES:\n"
            "{node_labels}" if node_labels else "",
            "Use only the following allowed relation types:\n# RELATION TYPES:\n"
            "{rel_types}" if rel_types else "",
            "Relations must respect the allowed schema, following the format: "
            "(EntityType1, RELATION_TYPE, EntityType2).\n"
            f"The defined schema is: {rel_types}" if relationship_type == "tuple" else "",
            "Below are examples of text with their extracted legal entities and relations:\n"
            "{examples}\n",
            additional_instructions,
            "For the text below, extract entities and relations exactly as shown in the example:\n"
            "{format_instructions}\nText: {input}",
        ]

        human_prompt_string = "\n".join(filter(None, human_string_parts))
        human_prompt = PromptTemplate(
            template=human_prompt_string,
            input_variables=["input"],
            partial_variables={
                "format_instructions": parser.get_format_instructions(),
                "node_labels": node_labels,
                "rel_types": rel_types,
                "examples": examples,
            },
        )

        human_message_prompt = HumanMessagePromptTemplate(prompt=human_prompt)

        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message, human_message_prompt]
        )
        return chat_prompt

    @staticmethod
    def _read(key: str) -> str:
        _ext = key.split('.')[-1].lower()
        if _ext == 'pdf':
            loader = AmazonTextractPDFLoader(
                f"s3://{env.S3_BUCKET_NAME}/{key}",
                region_name=env.AWS_REGION,
            )
            return "\n".join([page.page_content for page in loader.load()])
        elif _ext == 'txt' or _ext == 'md':
            loader = S3FileLoader(
                env.S3_BUCKET_NAME,
                key=key,
                region_name=env.AWS_REGION,
                aws_access_key_id=env.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
            )
            return "\n".join([page.page_content for page in loader.load()])
        raise RuntimeError(f"Unsupported file type: {_ext}")

    def update(self, key: str):
        """
        Update the knowledge base with the given S3 object ID.
        :param key:
        :return:
        """
        return # TODO: Implement this method
        # Load the document from S3
        contents = self._read(key)
        # Split the document into smaller chunks
        texts = self._splitter.split_text(contents)
        # Create Document objects from the split texts
        documents = [Document(page_content=text, source=key.split('/')[-1]) for text in texts]
        print(f"{len(documents)} Chunks created from {key}.")

        # Convert the documents to graph documents using LLMGraphTransformer
        llm = ChatBedrock(
            temperature=0,
            model=env.BEDROCK_MODEL_ID,
            region=env.AWS_REGION,
            aws_access_key_id=env.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
        )
        llm_graph = LLMGraphTransformer(
            llm,
            allowed_nodes=nodes,
            allowed_relationships=relationships,
            prompt= self._create_unstructured_prompt(
                node_labels=nodes,
                rel_types=relationships,
            )
        )
        graph_documents = llm_graph.convert_to_graph_documents(documents)

        # Connect to Neo4j and add the graph documents
        graph = Neo4jGraph(url=env.NEO4J_URL, username=env.NEO4J_USERNAME, password=env.NEO4J_PASSWORD)
        graph.add_graph_documents(graph_documents, include_source=True)
        # Refresh the schema to ensure the new documents are indexed
        graph.refresh_schema()
        print(f"Knowledge base updated with {len(graph_documents)} documents from {key}.")