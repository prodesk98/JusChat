import hashlib
import json

from typing import Optional, cast, Dict, Any, Tuple, List, Union, Type, Literal
from uuid import uuid4

from langchain_community.document_loaders import S3FileLoader, AmazonTextractPDFLoader
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_experimental.graph_transformers.llm import UnstructuredRelation
from langchain_openai import ChatOpenAI
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
from langchain_aws import ChatBedrock
from langchain_neo4j import Neo4jGraph
from pydantic import BaseModel, Field

from config import env
from core.prompt import EXTRACT_ENTITIES_PROMPT
from schemas import LegalDocumentMetadata
from services import S3Client
from vectorstore import QdrantClientManager


examples_: list[dict[str, str]] = [
    {
        "text": "Maria Silva é autora em um processo contra a Empresa XYZ "
                "no Tribunal de Justiça de São Paulo.",
        "head": "Maria Silva",
        "head_type": "Person",
        "relation": "PARTY_TO",
        "tail": "Processo 1020304-55.2023.8.26.0100",
        "tail_type": "Legal_Case",
    },
    {
        "text": "A Empresa XYZ foi representada pelo escritório de advocacia Souza & Associados.",
        "head": "Souza & Associados",
        "head_type": "Organization",
        "relation": "REPRESENTS",
        "tail": "Empresa XYZ",
        "tail_type": "Organization",
    },
    {
        "text": "O processo está sendo julgado pelo Tribunal de Justiça de São Paulo.",
        "head": "Processo 1020304-55.2023.8.26.0100",
        "head_type": "Legal_Case",
        "relation": "HANDLED_BY",
        "tail": "Tribunal de Justiça de São Paulo",
        "tail_type": "Court",
    },
    {
        "text": "O Tribunal de Justiça de São Paulo está localizado na cidade de São Paulo.",
        "head": "Tribunal de Justiça de São Paulo",
        "head_type": "Court",
        "relation": "LOCATED_IN",
        "tail": "São Paulo",
        "tail_type": "Location",
    },
    {
        "text": "A petição inicial do processo faz referência ao Artigo 927 do Código Civil.",
        "head": "Petição Inicial",
        "head_type": "Legal_Document",
        "relation": "REFERS_TO",
        "tail": "Artigo 927",
        "tail_type": "Law_Article",
    },
    {
        "text": "A decisão judicial resultou em condenação por danos morais.",
        "head": "Decisão Judicial",
        "head_type": "Legal_Document",
        "relation": "RESULTS_IN",
        "tail": "Danos Morais",
        "tail_type": "Penalty",
    },
    {
        "text": "Foi interposto recurso de apelação pela Empresa XYZ.",
        "head": "Processo 1020304-55.2023.8.26.0100",
        "head_type": "Legal_Case",
        "relation": "HAS_ACTION",
        "tail": "Apelação 2030405-66.2023.8.26.0100",
        "tail_type": "Appeal",
    },
    {
        "text": "A audiência de instrução ocorreu no Fórum João Mendes.",
        "head": "Audiência de Instrução",
        "head_type": "Event",
        "relation": "HELD_ON",
        "tail": "Fórum João Mendes",
        "tail_type": "Location",
    },
    {
        "text": "O laudo pericial foi incluído como prova no processo.",
        "head": "Laudo Pericial",
        "head_type": "Evidence",
        "relation": "EVIDENCE_IN",
        "tail": "Processo 1020304-55.2023.8.26.0100",
        "tail_type": "Legal_Case",
    },
    {
        "text": "O juiz Pedro Almeida decidiu o processo em favor de Maria Silva.",
        "head": "Pedro Almeida",
        "head_type": "Person",
        "relation": "DECIDED_BY",
        "tail": "Processo 1020304-55.2023.8.26.0100",
        "tail_type": "Legal_Case",
    },
]

nodes_: list[str] = [
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

relationships_: list[str] = [
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

legal_document_metadata_keys_: list[str] = [
    # Document Identification
    "title",
    "type",
    "case_number",
    "document_number",
    "creation_date",
    "filing_date",
    "signature_date",
    "version",
    "place_of_issue",

    # Parties Involved
    "plaintiffs",
    "defendants",
    "lawyers",
    "bar_number",
    "legal_representatives",
    "judge_or_rapporteur",
    "third_parties",

    # Procedural Data
    "court",
    "jurisdiction",
    "district",
    "adjudicating_body",
    "case_class",
    "nature_of_action",
    "main_subject",
    "secondary_subjects",
    "case_progress",
    "case_stage",

    # Legal Information
    "legal_basis",
    "jurisprudence",
    "legal_thesis",
    "claims",
    "legal_reasoning",
    "provisions",
    "decision",
    "case_value",
    "attorney_fees",
]

def _get_additional_info(input_type: str) -> str:
    # Check if the input_type is one of the allowed values
    if input_type not in ["node", "relationship", "property"]:
        raise ValueError("input_type must be 'node', 'relationship', or 'property'")

    # Perform actions based on the input_type
    if input_type == "node":
        return (
            "Ensure you use basic or elementary types for node labels.\n"
            "For example, when you identify an entity representing a person, "
            "always label it as **'Person'**. Avoid using more specific terms "
            "like 'Mathematician' or 'Scientist'"
        )
    elif input_type == "relationship":
        return (
            "Instead of using specific and momentary types such as "
            "'BECAME_PROFESSOR', use more general and timeless relationship types "
            "like 'PROFESSOR'. However, do not sacrifice any accuracy for generality"
        )
    elif input_type == "property":
        return ""
    return ""

def optional_enum_field(
    enum_values: Optional[Union[List[str], List[Tuple[str, str, str]]]] = None,
    description: str = "",
    input_type: str = "node",
    llm_type: Optional[str] = None,
    relationship_type: Optional[str] = None,
    **field_kwargs: Any,
) -> Any:
    """Utility function to conditionally create a field with an enum constraint."""
    parsed_enum_values = enum_values
    # We have to extract enum types from tuples
    if relationship_type == "tuple":
        parsed_enum_values = list({el[1] for el in enum_values})  # type: ignore

    # Only openai supports enum param
    if enum_values and llm_type == "openai-chat":
        return Field( # noqa
            ...,
            enum=parsed_enum_values,  # type: ignore[call-arg]
            description=f"{description}. Available options are {parsed_enum_values}",
            **field_kwargs,
        )
    elif enum_values:
        return Field(
            ...,
            description=f"{description}. Available options are {parsed_enum_values}",
            **field_kwargs,
        )
    else:
        additional_info = _get_additional_info(input_type)
        return Field(..., description=description + additional_info, **field_kwargs)

DEFAULT_NODE_TYPE = "Node"

class _Graph(BaseModel):
    nodes: Optional[List]
    relationships: Optional[List]

def create_simple_model(
    node_labels: Optional[List[str]] = None,
    rel_types: Optional[Union[List[str], List[Tuple[str, str, str]]]] = None,
    node_properties: Union[bool, List[str]] = False,
    llm_type: Optional[str] = None,
    relationship_properties: Union[bool, List[str]] = False,
    relationship_type: Optional[str] = None, # noqa
) -> Type[_Graph]:
    """
    Create a simple graph model with optional constraints on node
    and relationship types.

    Args:
        node_labels (Optional[List[str]]): Specifies the allowed node types.
            Defaults to None, allowing all node types.
        rel_types (Optional[List[str]]): Specifies the allowed relationship types.
            Defaults to None, allowing all relationship types.
        node_properties (Union[bool, List[str]]): Specifies if node properties should
            be included. If a list is provided, only properties with keys in the list
            will be included. If True, all properties are included. Defaults to False.
        relationship_properties (Union[bool, List[str]]): Specifies if relationship
            properties should be included. If a list is provided, only properties with
            keys in the list will be included. If True, all properties are included.
            Defaults to False.
        llm_type (Optional[str]): The type of the language model. Defaults to None.
            Only openai supports enum param: openai-chat.

    Returns:
        Type[_Graph]: A graph model with the specified constraints.

    Raises:
        ValueError: If 'id' is included in the node or relationship properties list.
    """

    node_fields: Dict[str, Tuple[Any, Any]] = {
        "id": (
            str,
            Field(..., description="Name or human-readable unique identifier."),
        ),
        "type": (
            str,
            optional_enum_field(
                node_labels,
                description="The type or label of the node.",
                input_type="node",
                llm_type=llm_type,
            ),
        ),
    }

    if node_properties:
        if isinstance(node_properties, list) and "id" in node_properties:
            raise ValueError("The node property 'id' is reserved and cannot be used.")
        # Map True to empty array
        node_properties_mapped: List[str] = (
            [] if node_properties is True else node_properties
        )

        class Property(BaseModel):
            """A single property consisting of key and value"""

            key: str = optional_enum_field(
                node_properties_mapped,
                description="Property key.",
                input_type="property",
                llm_type=llm_type,
            )
            value: str = Field(
                ...,
                description=(
                    "Extracted value. Any date value "
                    "should be formatted as yyyy-mm-dd."
                ),
            )

        node_fields["properties"] = (
            Optional[List[Property]],
            Field(None, description="List of node properties"),
        )
    SimpleNode = create_model("SimpleNode", **node_fields)  # type: ignore

    relationship_fields: Dict[str, Tuple[Any, Any]] = {
        "source_node_id": (
            str,
            Field(
                ...,
                description="Name or human-readable unique identifier of source node",
            ),
        ),
        "source_node_type": (
            str,
            optional_enum_field(
                node_labels,
                description="The type or label of the source node.",
                input_type="node",
                llm_type=llm_type,
            ),
        ),
        "target_node_id": (
            str,
            Field(
                ...,
                description="Name or human-readable unique identifier of target node",
            ),
        ),
        "target_node_type": (
            str,
            optional_enum_field(
                node_labels,
                description="The type or label of the target node.",
                input_type="node",
                llm_type=llm_type,
            ),
        ),
        "type": (
            str,
            optional_enum_field(
                rel_types,
                description="The type of the relationship.",
                input_type="relationship",
                llm_type=llm_type,
                relationship_type=relationship_type,
            ),
        ),
    }
    if relationship_properties:
        if (
            isinstance(relationship_properties, list)
            and "id" in relationship_properties
        ):
            raise ValueError(
                "The relationship property 'id' is reserved and cannot be used."
            )
        # Map True to empty array
        relationship_properties_mapped: List[str] = (
            [] if relationship_properties is True else relationship_properties
        )

        class RelationshipProperty(BaseModel):
            """A single property consisting of key and value"""

            key: str = optional_enum_field(
                relationship_properties_mapped,
                description="Property key.",
                input_type="property",
                llm_type=llm_type,
            )
            value: str = Field(
                ...,
                description=(
                    "Extracted value. Any date value "
                    "should be formatted as yyyy-mm-dd."
                ),
            )

        relationship_fields["properties"] = (
            Optional[List[RelationshipProperty]],
            Field(None, description="List of relationship properties"),
        )
    SimpleRelationship = create_model("SimpleRelationship", **relationship_fields)  # type: ignore
    # Add a docstring to the dynamically created model
    if relationship_type == "tuple":
        SimpleRelationship.__doc__ = (
            "Your task is to extract relationships from text strictly adhering "
            "to the provided schema. The relationships can only appear "
            "between specific node types are presented in the schema format "
            "like: (Entity1Type, RELATIONSHIP_TYPE, Entity2Type) /n"
            f"Provided schema is {rel_types}"
        )

    class DynamicGraph(_Graph):
        """Represents a graph document consisting of nodes and relationships."""

        nodes: Optional[List[SimpleNode]] = Field(description="List of nodes")  # type: ignore
        relationships: Optional[List[SimpleRelationship]] = Field(  # type: ignore
            description="List of relationships"
        )

    return DynamicGraph


def map_to_base_node(node: Any) -> Node:
    """Map the SimpleNode to the base Node."""
    properties = {}
    if hasattr(node, "properties") and node.properties:
        for p in node.properties:
            properties[format_property_key(p.key)] = p.value
    return Node(id=node.id, type=node.type, properties=properties)


def map_to_base_relationship(rel: Any) -> Relationship:
    """Map the SimpleRelationship to the base Relationship."""
    source = Node(id=rel.source_node_id, type=rel.source_node_type)
    target = Node(id=rel.target_node_id, type=rel.target_node_type)
    properties = {}
    if hasattr(rel, "properties") and rel.properties:
        for p in rel.properties:
            properties[format_property_key(p.key)] = p.value
    return Relationship(
        source=source, target=target, type=rel.type, properties=properties
    )


def _parse_and_clean_json(
    argument_json: Dict[str, Any],
) -> Tuple[List[Node], List[Relationship]]:
    nodes = []
    for node in argument_json["nodes"]:
        if not node.get("id"):  # Id is mandatory, skip this node
            continue
        node_properties = {}
        if "properties" in node and node["properties"]:
            for p in node["properties"]:
                node_properties[format_property_key(p["key"])] = p["value"]
        nodes.append(
            Node(
                id=node["id"],
                type=node.get("type", DEFAULT_NODE_TYPE),
                properties=node_properties,
            )
        )
    relationships = []
    for rel in argument_json["relationships"]:
        # Mandatory props
        if (
            not rel.get("source_node_id")
            or not rel.get("target_node_id")
            or not rel.get("type")
        ):
            continue

        # Node type copying if needed from node list
        if not rel.get("source_node_type"):
            try:
                rel["source_node_type"] = [
                    el.get("type")
                    for el in argument_json["nodes"]
                    if el["id"] == rel["source_node_id"]
                ][0]
            except IndexError:
                rel["source_node_type"] = DEFAULT_NODE_TYPE
        if not rel.get("target_node_type"):
            try:
                rel["target_node_type"] = [
                    el.get("type")
                    for el in argument_json["nodes"]
                    if el["id"] == rel["target_node_id"]
                ][0]
            except IndexError:
                rel["target_node_type"] = DEFAULT_NODE_TYPE

        rel_properties = {}
        if "properties" in rel and rel["properties"]:
            for p in rel["properties"]:
                rel_properties[format_property_key(p["key"])] = p["value"]

        source_node = Node(
            id=rel["source_node_id"],
            type=rel["source_node_type"],
        )
        target_node = Node(
            id=rel["target_node_id"],
            type=rel["target_node_type"],
        )
        relationships.append(
            Relationship(
                source=source_node,
                target=target_node,
                type=rel["type"],
                properties=rel_properties,
            )
        )
    return nodes, relationships


def _format_nodes(nodes: List[Node]) -> List[Node]:
    return [
        Node(
            id=el.id.title() if isinstance(el.id, str) else el.id,
            type=el.type.capitalize()  # type: ignore[arg-type]
            if el.type
            else DEFAULT_NODE_TYPE,  # handle empty strings  # type: ignore[arg-type]
            properties=el.properties,
        )
        for el in nodes
    ]


def _format_relationships(rels: List[Relationship]) -> List[Relationship]:
    return [
        Relationship(
            source=_format_nodes([el.source])[0],
            target=_format_nodes([el.target])[0],
            type=el.type.replace(" ", "_").upper(),
            properties=el.properties,
        )
        for el in rels
    ]


def format_property_key(s: str) -> str:
    words = s.split()
    if not words:
        return s
    first_word = words[0].lower()
    capitalized_words = [word.capitalize() for word in words[1:]]
    return "".join([first_word] + capitalized_words)


def _convert_to_graph_document(
    raw_schema: Dict[Any, Any],
) -> Tuple[List[Node], List[Relationship]]:
    # If there are validation errors
    if not raw_schema["parsed"]:
        try:
            try:  # OpenAI type response
                argument_json = json.loads(
                    raw_schema["raw"].additional_kwargs["tool_calls"][0]["function"][
                        "arguments"
                    ]
                )
            except Exception:  # noqa
                try:
                    argument_json = json.loads(
                        raw_schema["raw"].additional_kwargs["function_call"][
                            "arguments"
                        ]
                    )
                except Exception:  # noqa
                    argument_json = raw_schema["raw"].tool_calls[0]["args"]
                    if isinstance(argument_json["nodes"], str):
                        argument_json["nodes"] = json.loads(argument_json["nodes"])
                    if isinstance(argument_json["relationships"], str):
                        argument_json["relationships"] = json.loads(
                            argument_json["relationships"]
                        )
            nodes, relationships = _parse_and_clean_json(argument_json)
        except Exception:  # noqa
            return [], []
    else:  # If there are no validation errors use parsed pydantic object
        parsed_schema: _Graph = raw_schema["parsed"]
        nodes = (
            [map_to_base_node(node) for node in parsed_schema.nodes if node.id]
            if parsed_schema.nodes
            else []
        )

        relationships = (
            [
                map_to_base_relationship(rel)
                for rel in parsed_schema.relationships
                if rel.type and rel.source_node_id and rel.target_node_id
            ]
            if parsed_schema.relationships
            else []
        )
    # Title / Capitalize
    return _format_nodes(nodes), _format_relationships(relationships)


BATCH_SIZE = 10 # Number of documents to process in a batch


class LLMGraph(LLMGraphTransformer):
    def __init__(self, llm: BaseLanguageModel, prompt: Optional[ChatPromptTemplate] = None):
        """
        Initialize the LLMGraph with a language model.
        :param llm: The language model to use for processing.
        """
        super().__init__(llm=llm, allowed_nodes=nodes_, allowed_relationships=relationships_, prompt=prompt)

    def process_batch(
        self, documents: list[Document], config: Optional[RunnableConfig] = None
    ) -> list[GraphDocument]:
        """
        Process a batch of documents and extract graph information.
        :param documents:
        :param config:
        :return:
        """
        graph_documents: list[GraphDocument] = []
        for batch in range(0, len(documents), BATCH_SIZE):
            docs = documents[batch:batch + BATCH_SIZE]
            results_batch = self.chain.batch(
                docs,
                config=config,
            )
            for i, raw_schema in enumerate(results_batch):
                if self._function_call:
                    raw_schema = cast(Dict[Any, Any], raw_schema)
                    nodes, relationships = _convert_to_graph_document(raw_schema)
                else:
                    nodes_set = set()
                    relationships = []
                    if not isinstance(raw_schema, str):
                        raw_schema = raw_schema.content
                    parsed_json = self.json_repair.loads(raw_schema)
                    if isinstance(parsed_json, dict):
                        parsed_json = [parsed_json]
                    for rel in parsed_json:
                        # Check if mandatory properties are there
                        if (
                            not isinstance(rel, dict)
                            or not rel.get("head")
                            or not rel.get("tail")
                            or not rel.get("relation")
                        ):
                            continue
                        # Nodes need to be deduplicated using a set
                        # Use default Node label for nodes if missing
                        nodes_set.add((rel["head"], rel.get("head_type", DEFAULT_NODE_TYPE)))
                        nodes_set.add((rel["tail"], rel.get("tail_type", DEFAULT_NODE_TYPE)))

                        source_node = Node(
                            id=rel["head"], type=rel.get("head_type", DEFAULT_NODE_TYPE)
                        )
                        target_node = Node(
                            id=rel["tail"], type=rel.get("tail_type", DEFAULT_NODE_TYPE)
                        )
                        relationships.append(
                            Relationship(
                                source=source_node, target=target_node, type=rel["relation"]
                            )
                        )
                    # Create nodes list
                    nodes = [Node(id=el[0], type=el[1]) for el in list(nodes_set)]

                # Strict mode filtering
                if self.strict_mode and (self.allowed_nodes or self.allowed_relationships):
                    if self.allowed_nodes:
                        lower_allowed_nodes = [el.lower() for el in self.allowed_nodes]
                        nodes = [
                            node for node in nodes if node.type.lower() in lower_allowed_nodes
                        ]
                        relationships = [
                            rel
                            for rel in relationships
                            if rel.source.type.lower() in lower_allowed_nodes
                               and rel.target.type.lower() in lower_allowed_nodes
                        ]
                    if self.allowed_relationships:
                        # Filter by type and direction
                        if self._relationship_type == "tuple":
                            relationships = [
                                rel
                                for rel in relationships
                                if (
                                        (
                                            rel.source.type.lower(),
                                            rel.type.lower(),
                                            rel.target.type.lower(),
                                        )
                                        in [  # type: ignore
                                            (s_t.lower(), r_t.lower(), t_t.lower())
                                            for s_t, r_t, t_t in self.allowed_relationships
                                        ]
                                )
                            ]
                        else:  # Filter by type only
                            relationships = [
                                rel
                                for rel in relationships
                                if rel.type.lower()
                                   in [el.lower() for el in self.allowed_relationships]  # type: ignore
                            ]
                graph_documents.append(GraphDocument(nodes=nodes, relationships=relationships, source=documents[i]))
        return graph_documents

class KnowledgeService:
    def __init__(self):
        self._splitter = CharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=300,
            chunk_overlap=50,
        )

    @staticmethod
    def calc_document_hash(contents: str) -> str:
        """
        Calculate a hash for the document contents.
        :param contents: The document contents as bytes.
        :return: A string representing the hash of the document.
        """
        return hashlib.sha256(contents.encode()).hexdigest()

    @staticmethod
    def get_document_id() -> str:
        """
        Generate a unique document ID based on the current timestamp.
        :return: A string representing the document ID.
        """
        return uuid4().hex

    def process_response(
        self, document: list[Document], config: Optional[RunnableConfig] = None
    ) -> list[GraphDocument]:
        ...

    @staticmethod
    def _create_unstructured_relationships_prompt(
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
                "examples": examples_,
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

    @staticmethod
    def _get_llm(llm_name: Literal['openai', 'bedrock'] = 'bedrock') -> BaseLanguageModel:
        """
        Get the LLM instance based on the specified type.
        :param llm_name: The type of LLM to use ('openai' or 'bedrock').
        :return: An instance of the specified LLM.
        """
        if llm_name == 'openai':
            return ChatOpenAI(
                temperature=0,
                model=env.BEDROCK_MODEL_ID,
                max_tokens=2048,
            )
        elif llm_name == 'bedrock':
            return ChatBedrock(
                temperature=0,
                model=env.BEDROCK_MODEL_ID,
                region=env.AWS_REGION,
                aws_access_key_id=env.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
            )
        raise ValueError("Unsupported LLM type. Use 'openai' or 'bedrock'.")

    def process(self, key: str):
        """
        Process a document from S3, split it into chunks, and add it to the knowledge base.
        :param key:
        :return:
        """
        # Load the document from S3
        contents = self._read(key)
        # Split the document into smaller chunks
        texts = self._splitter.split_text(contents)
        # Create Document objects from the split texts
        source = key.split('/')[-1]
        documents = [Document(id=uuid4().hex, page_content=text, source=source) for text in texts]
        print(f"{len(documents)} Chunks created from {key}.")

        # Convert the documents to graph documents using LLMGraphTransformer
        llm = self._get_llm()
        # Create the LLMGraphTransformer with the allowed nodes and relationships
        llm_graph = LLMGraph(llm)
        graph_documents = llm_graph.process_batch(documents)

        # Connect to Neo4j and add the graph documents
        graph = Neo4jGraph(url=env.NEO4J_URL, username=env.NEO4J_USERNAME, password=env.NEO4J_PASSWORD)
        graph.add_graph_documents(graph_documents, include_source=True)
        # Refresh the schema to ensure the new documents are indexed
        graph.refresh_schema()

        # Calculate the document hash
        document_hash = self.calc_document_hash(contents)
        document_id = self.get_document_id()
        # Update the metadata with the extracted information
        metadatas: dict[str, list[str]|str] = {
            "document_id": document_id,
            "document_hash": document_hash,
            "source": source,
        }
        # Extract metadata from the document using the LLM
        structured = llm.with_structured_output(LegalDocumentMetadata)
        chain_legal_document = EXTRACT_ENTITIES_PROMPT | structured
        # Iterate over the texts and extract metadata
        for text in texts:
            # Extract metadata from the document
            metadata_extraction_result: LegalDocumentMetadata = chain_legal_document.invoke( # type: ignore
                {"entities": ", ".join(legal_document_metadata_keys_), "text": text})
            # Parse the metadata extraction result
            metadata: dict = metadata_extraction_result.model_dump(exclude_none=True)
            for k in metadata.keys():
                if k in ['document_id', 'document_hash', 'source']: continue
                if k in list(metadatas.keys()):
                    if isinstance(metadatas[k], list):
                        metadatas[k].extend(metadata[k])
                        continue
                    if isinstance(metadatas[k], str):
                        metadatas[k] += "\n" + metadata[k]
                else:
                    metadatas[k] = metadata[k]

        # Add the document to the vector database
        vectorstore = QdrantClientManager()
        # Build the Document objects with the metadata
        documents = [
            Document(
                id=doc.id,
                page_content=doc.page_content,
                metadata=metadatas
            ) for doc in documents
        ]
        # Add the documents to the vector database
        vectorstore.add_documents(documents=documents)
        # Delete object from S3
        S3Client().delete_object(key)
        # Log the update
        print(f"Knowledge base updated with {len(documents)} documents from {key}.")