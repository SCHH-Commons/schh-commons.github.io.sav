#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
import asyncio
import requests

import pinecone
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

# LangChain imports
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone as LC_Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import RetrievalQA

# For streaming responses over HTTP
from sse_starlette.sse import EventSourceResponse

#############################################
# Global In‑Memory Conversation Memory Store
#############################################
# This dictionary maps a session_id (string) to a list of conversation turns.
# Each turn is stored as a string (e.g., "Q: <question>\nA: <answer>").
chat_memories = {}

##############################
# 1. Define a Weather Tool
##############################
def get_current_weather(location: str, unit: str = "Celsius") -> str:
    """
    Fetch current weather information for a given location.
    (Using wttr.in as a demo API in place of Tavily.)
    """
    try:
        response = requests.get(f"https://wttr.in/{location}?format=3")
        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"Could not fetch weather data for {location}."
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"

# Wrap the weather function as a LangChain Tool.
weather_tool = Tool(
    name="get_current_weather",
    func=get_current_weather,
    description=(
        "Useful for when you need to get the current weather information for a location. "
        "The input to this tool should be a location name (for example, 'Paris')."
    )
)

##############################
# 2. Build the Chatbot Assistant with Memory
##############################
class ChatbotAssistant:
    def __init__(self, streaming: bool = False):
        self.streaming = streaming

        # Set up streaming callbacks if streaming is enabled.
        callbacks = [StreamingStdOutCallbackHandler()] if streaming else []

        # Initialize the language model.
        self.llm = ChatOpenAI(
            model_name="gpt-4o",
            streaming=streaming,
            callbacks=callbacks,
            temperature=0.0,
        )

        # Set up OpenAI embeddings.
        self.embeddings = OpenAIEmbeddings()

        # Connect to the existing Pinecone index.
        self.vectorstore = LC_Pinecone.from_existing_index(
            index_name='schh',
            embedding=self.embeddings,
            text_key="text"  # Assumes documents are indexed under the "text" field.
        )

        # Build a RetrievalQA chain that uses the Pinecone vectorstore.
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",  # "stuff" simply concatenates documents.
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=True,
        )

        # Initialize an agent that has access to the weather tool.
        self.agent = initialize_agent(
            tools=[weather_tool],
            llm=self.llm,
            agent="zero-shot-react-description",
            verbose=True,
        )

    def answer_query(self, query: str, session_id: Optional[str] = None) -> dict:
        """
        Answer the given query while considering previous conversation turns if provided.

        If the session_id is provided and conversation history exists,
        that history is prepended to the query for context.
        For weather‑related queries, the agent (with the weather tool) is used.
        For other queries, the RetrievalQA (RAG) chain is used.

        The new Q/A pair is appended to the conversation history.
        
        Returns:
            dict: { "answer": <text>, "sources": [<source1>, ...] }
        """
        original_query = query  # Preserve the original question.
        # If conversation memory exists for this session, prepend it to the query.
        if session_id is not None:
            history = chat_memories.get(session_id, [])
            if history:
                # You can customize how the conversation history is injected.
                context = "\n".join(history)
                query = f"Conversation History:\n{context}\n\nNew Question: {query}"

        # Use the weather tool if the query mentions weather.
        if "weather" in original_query.lower():
            answer = self.agent.run(query)
            result = {"answer": answer, "sources": []}
        else:
            chain_result = self.qa_chain(query)
            answer = chain_result.get("result", "")
            sources = []
            for doc in chain_result.get("source_documents", []):
                source_info = doc.metadata.get("source", "Unknown source")
                sources.append(source_info)
            result = {"answer": answer, "sources": sources}

        # Update conversation memory for this session.
        if session_id is not None:
            # Here we store the original question (without the prepended history) and the answer.
            memory_entry = f"Q: {original_query}\nA: {answer}"
            if session_id in chat_memories:
                chat_memories[session_id].append(memory_entry)
            else:
                chat_memories[session_id] = [memory_entry]
        return result

##############################
# 3. Set Up FastAPI Endpoints with Session IDs
##############################
app = FastAPI()

# Initialize the assistant (defaulting to non-streaming mode).
assistant = ChatbotAssistant(streaming=False)

# Pydantic models for request/response bodies.
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # Client can supply a session ID.
    streaming: Optional[bool] = False  # Client can request streaming output.

class QueryResponse(BaseModel):
    answer: str
    sources: List[str] = []
    session_id: str  # Return the session ID so that the client can continue the conversation.

@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    """
    Synchronous (non‑streaming) endpoint.
    If the client does not supply a session_id, a new one is generated.
    """
    global assistant
    # Reinitialize assistant if the streaming flag differs.
    if request.streaming != assistant.streaming:
        assistant = ChatbotAssistant(streaming=request.streaming)
    # Generate a session ID if none is provided.
    session_id = request.session_id or str(uuid.uuid4())
    result = assistant.answer_query(request.query, session_id=session_id)
    return QueryResponse(answer=result["answer"], sources=result["sources"], session_id=session_id)

#############################################
# 4. Streaming Endpoint with Memory (SSE)
#############################################
# Define a custom callback handler that uses an asyncio.Queue.
class QueueCallbackHandler(StreamingStdOutCallbackHandler):
    def __init__(self):
        super().__init__()
        self.queue = asyncio.Queue()

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        asyncio.create_task(self.queue.put(token))

async def stream_tokens(query: str, session_id: Optional[str] = None):
    """
    A generator that streams tokens as SSE events.
    Conversation history (if any) is prepended to the query.
    """
    original_query = query
    if session_id is not None:
        history = chat_memories.get(session_id, [])
        if history:
            context = "\n".join(history)
            query = f"Conversation History:\n{context}\n\nNew Question: {query}"
    handler = QueueCallbackHandler()
    llm_stream = ChatOpenAI(
        model_name="gpt-4",
        streaming=True,
        callbacks=[handler],
        temperature=0.0,
    )
    # Choose the chain based on the query.
    if "weather" in original_query.lower():
        agent = initialize_agent(
            tools=[weather_tool],
            llm=llm_stream,
            agent="zero-shot-react-description",
            verbose=True,
        )
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, agent.run, query)
    else:
        retrieval_chain = RetrievalQA.from_chain_type(
            llm=llm_stream,
            chain_type="stuff",
            retriever=assistant.vectorstore.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=True,
        )
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, retrieval_chain, query)

    # Collect streamed tokens.
    answer_parts = []
    while True:
        try:
            token = await asyncio.wait_for(handler.queue.get(), timeout=1.0)
            answer_parts.append(token)
            yield f"data: {token}\n\n"
        except asyncio.TimeoutError:
            if future.done():
                break
    answer = "".join(answer_parts)
    # Update conversation memory.
    if session_id is not None:
        memory_entry = f"Q: {original_query}\nA: {answer}"
        if session_id in chat_memories:
            chat_memories[session_id].append(memory_entry)
        else:
            chat_memories[session_id] = [memory_entry]
    yield "data: [DONE]\n\n"

@app.post("/chat/stream")
async def chat_stream_endpoint(request: QueryRequest):
    """
    Streaming endpoint that returns tokens via Server‑Sent Events (SSE).
    A session_id is used to store conversation history.
    """
    session_id = request.session_id or str(uuid.uuid4())
    return EventSourceResponse(stream_tokens(request.query, session_id=session_id))

##############################
# 5. Run with Uvicorn
##############################
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)