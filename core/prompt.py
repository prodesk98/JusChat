from langchain.prompts import PromptTemplate


ROUTING_CONSTANTS = {
    "search_graph": "Consultando os relacionamentos do grafo",
    "search_vector": "Consultando o contexto semântico",
    "generate_subqueries": "Gerando novas sub-consultas",
    "answer_final": "Concluído! Gerando resposta final",
}


CYPHER_PROMPT = PromptTemplate(
    template="""You are an expert at generating Cypher queries for Neo4j.
Use the following schema to generate a Cypher query that answers the given question.
Make the query flexible by using case-insensitive matching and partial string matching where appropriate.
Focus on searching paper titles as they contain the most relevant information.

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Do not use any other relationship types or properties that are not provided.

Chat history:
---
{{chat_history}}
---

Schema:
{schema}

The question is: 
{question}

Cypher:""",
    input_variables=["schema", "question"],
)

QA_PROMPT = PromptTemplate(
    template="""You are a legal evaluator.

Check if the answer is consistent with the question and the provided context only.
Use no extra knowledge.
Classify the answer as: 'Coherent Document', 'Incomplete Document', or 'Unrelated Document'.

Context:
{context}

Question:
{question}

Classification:""",
    input_variables=["question", "context"],
)

START_PROMPT = PromptTemplate(
    template="""You are a legal expert assistant.  
Your task is to decide if the user’s legal question can be answered directly using existing knowledge or if it requires retrieving additional information from external sources.  

You have two options:  
1. **'needs_search'** — Use when the question requires checking documents, legal databases, or any additional context before answering.  
2. **'answer_final'** — Use only if the question is clear and you already have enough information to answer without any further search.

---

**Rule:**  
- Choose **'needs_search'** if any part of the question depends on specific legal details, facts, or context that must be looked up.  
- Choose **'answer_final'** if the question can be answered confidently with general legal knowledge, definitions, or a simple statement.

Return only **'needs_search'** or **'answer_final'**.

---

**Question:**  
{question}""",
    input_variables=["question"],
)

ROUTING_PROMPT = PromptTemplate(
    template="""You are a legal expert specializing in routing a user’s legal question to the most appropriate next action.

You have three options:
1. **'search_graph'** — Use when the question requires structured, explicit relationships between legal entities, such as people, courts, or articles, or when the answer depends on navigating clear links in the knowledge graph.
2. **'search_vector'** — Use when the question is open-ended, vague, uses synonyms or natural language, and would benefit from semantic similarity matching to find relevant context not directly connected in the graph.
3. **'answer_final'** — Use only if the information is already complete and no further search is needed.

---

**Rule:**

* Prefer **'search_graph'** for specific, explicit relationships (e.g., *"Which articles relate to this law?"*, *"Who filed the appeal?"*).
* Prefer **'search_vector'** for broad, general, or ambiguous questions (e.g., *"What does this concept mean?"*, *"Explain the context of this case."*).
* Use **'answer_final'** only if the information is sufficient and no more search is required.

---

**Documents to consider:**
{documents}

**Question to route:**
{question}""",
    input_variables=["documents", "question"],
)

SUBQUERIES_PROMPT = PromptTemplate(
    template="""You are a legal assistant that breaks down a complex legal question into smaller, clear, and specific sub-questions.
Generate only sub-questions that help clarify or expand the main question into logical parts.
Each sub-question must be unique and must not repeat the same meaning as another already generated.
If the main question is already simple and does not need to be broken down, return an empty list.
Do not add any explanations or extra text.

Main legal question:
{question}

Already generated sub-questions:
{subqueries}""",
    input_variables=["question", "subqueries"],
)

ASSISTANT_PROMPT = PromptTemplate(
    template="""Você é um assistente jurídico responsável por fornecer respostas claras, objetivas e fundamentadas a perguntas legais.
Utilize exclusivamente as informações do contexto fornecido para elaborar sua resposta.
Caso o contexto esteja vazio ou não contenha detalhes suficientes, informe educadamente que não há informações suficientes para responder à pergunta.

Informações disponíveis:
{context}""",
    input_variables=["context"],
)

EXTRACT_ENTITIES_PROMPT = PromptTemplate(
    template="""You are a legal extraction assistant specialized in the Brazilian legal domain. 
Your task is to extract structured legal information from text in order to build a Brazilian legal knowledge graph. 
Identify legal entities strictly following the user prompt. 

You must produce output in JSON format, containing a single JSON object with the keys: 
If something is missing, leave it empty or null. Do not guess or hallucinate. Extract precisely.
{entities}. Use only the explicit information in the text.

Extract the following legal entities from the provided text:
{text}
""",
    input_variables=["entities", "text"],
)