from langchain.prompts import PromptTemplate

CYPHER_PROMPT = PromptTemplate(
    template="""You are an expert at generating Cypher queries for Neo4j.
Use the following schema to generate a Cypher query that answers the given question.
Make the query flexible by using case-insensitive matching and partial string matching where appropriate.
Focus on searching paper titles as they contain the most relevant information.

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Do not use any other relationship types or properties that are not provided.

Schema:
{schema}

The question is: 
{question}""",
    input_variables=["schema", "question"],
)

QA_PROMPT = PromptTemplate(
    template="""You are an assistant that helps to form clear and legally sound answers.
The information part contains the provided legal information that you must use to construct an answer.
The provided information is authoritative; you must never doubt it or try to use your internal knowledge to correct it.
Make the answer sound as a direct response to the question. Do not mention that you based the result on the given information.
Here is an example:

Question: Which lawyers represent the defendant?
Context: [lawyer: JOHN DOE, lawyer: SMITH & PARTNERS LLP]
Helpful Answer: JOHN DOE and SMITH & PARTNERS LLP represent the defendant.

Follow this example when generating answers.
If the provided information is empty, say that you don't know the answer.
Information:
{context}

Question: {question}
Helpful Answer:""",
    input_variables=["question", "context"],
)

ROUTING_PROMPT = PromptTemplate(
    template="""You are a legal expert specializing in routing a user’s legal question to the most appropriate next action.
You have two options:
1. 'generate_subqueries': Use when the answer could benefit from generating additional sub-queries to refine or expand the legal information retrieved.
2. 'answer_final': Use when the current answer is already correct and complete, and no more legal information is needed.

Decide which option is most appropriate based on the nature of the legal question, the provided sub-queries, and the available documents.
The value must be either 'generate_subqueries' or 'answer_final'.
Before choosing 'generate_subqueries', ensure that new sub-queries do not duplicate existing ones or repeat the same intent.

Documents to consider:
{documents}

Question to route:
{question}""",
    input_variables=["documents", "question"],
)

SUBQUERY_PROMPT = PromptTemplate(
    template="""You are a legal assistant that breaks down a complex legal question into smaller, clear sub-questions.
Generate only sub-questions that help clarify or expand the main question into logical parts.
Each sub-question must be unique and not repeat the same meaning as another.
If the question is already simple and does not need to be broken down, return an empty list.
Return the sub-questions as a JSON array under the key 'subquestions'. Do not add any explanation or extra text.

Main legal question:
{question}""",
    input_variables=["question"],
)