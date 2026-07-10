# Government Services QA Skill

A RAG-based government services question answering skill that can be installed into TeleAgent.

## Description

This skill enables TeleAgent to answer citizen questions about government services, including household registration (户籍), social security (社保), housing provident fund (公积金), property registration (不动产), and more.

It uses a FAISS vector knowledge base with LangChain RAG chain for accurate, evidence-based answers.

## Capabilities

- **gov_qa_answer**: Answer a government service question using RAG retrieval
- **gov_qa_search**: Search the knowledge base for relevant documents
- **gov_qa_upload**: Upload new documents to the knowledge base

## Usage

After installing this skill, you can ask TeleAgent questions like:

- "新生儿落户需要什么材料？"
- "社保怎么从外地转过来？"
- "公积金贷款最高额度是多少？"

The agent will retrieve relevant information from the knowledge base and provide accurate answers with source references.

## Configuration

Requires the following environment variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | LLM API key |
| `OPENAI_API_BASE` | LLM API base URL |
| `OPENAI_MODEL_NAME` | Model name (default: gpt-4o-mini) |
| `EMBEDDING_MODEL_NAME` | Embedding model name |
| `EMBEDDING_API_BASE` | Embedding API base URL |

## Architecture

```
User Question
    │
    ▼
┌──────────────┐
│  FAISS Retriever  │ ── Top-K similar documents
└──────────────┘
    │
    ▼
┌──────────────┐
│  RAG Prompt   │ ── Inject context + question
└──────────────┘
    │
    ▼
┌──────────────┐
│  LLM (Chat)   │ ── Generate answer
└──────────────┘
    │
    ▼
Answer + Sources
```
