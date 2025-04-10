# Create Daca

**Template with Prebuilt Chat Agent, Memory Agent built using OpenAI Agents SDK, Event-Driven Communication, Distributed Runtime, and Simplicity at its core.**

> **Note**: <span style="color: orange;">This is an educational and experimental template designed to explore agentic systems with Dapr, UV, and an agent engine like OpenAI Agents SDK. Use it to learn and experiment!</span>

<p> A UV-based template for **developing and deploying agentic systems**—autonomous, AI-driven agents powered by a **distributed runtime foundation** with Dapr. Featuring a **Chat Agent** and a **Memory Agent**, built with the OpenAI Agents SDK, this package offers a simple, flexible base for agent-driven projects. It works with any agent engine (e.g., LangGraph, CrewAI, Dapr Agents, or pure Python) and scales from local tinkering to cloud deployment. Dive into the code below to see how it works! </p>
---

## Quick Start 

1. **Install**:
```bash
   uvx create-daca my-new-project
   cd my-new-project
```
2. Run (after setting GEMINI_API_KEY in .env files—see below):
```bash
dapr init
cd agent_memory_service && uv sync && uv add openai-agents && dapr run --app-id agent-memory-service --app-port 8001 --dapr-http-port 3501 --resources-path ../components -- uv run uvicorn main:app --reload &
cd chat_service && uv sync && dapr run --app-id chat-service --app-port 8010 --dapr-http-port 3500 --resources-path ../components -- uv run uvicorn main:app --reload
```
3. Chat
Open locahost:8010/docs and localhost:8001/docs or in terminal
   - Initialize memory:
     ```bash
     curl -X POST http://localhost:8001/memories/junaid/initialize -H "Content-Type: application/json" -d '{"name": "Junaid", "preferred_style": "formal", "user_summary": "Junaid is a new user."}'
     ```
   - Chat:
     ```bash
     curl -X POST http://localhost:8010/chat/ -H "Content-Type: application/json" -d '{"user_id": "junaid", "text": "Hello"}'
     ```

## What It Offers
- **Chat Agent**: Handles user interactions with LLM-powered responses, publishing events for collaboration.
- **Memory Agent**: Persists and enriches agent memory with dynamic LLM insights.
- **Distributed Runtime**: Dapr ensures resilience and scalability via Pub/Sub and state management.
- **Development Ready**: Build and test agents locally with UV.
- **Deployable**: Scale to distributed systems with Dapr’s runtime.
- **Flexible**: Swap in any agent engine for custom workflows.

Derived from [Step 7 of the Panaversity **Dapr Agentic Cloud Ascent (DACA)** series](https://github.com/panaversity/learn-agentic-ai/tree/main/01_openai_agents/17_daca_local_dev), this is your foundation for agentic innovation.

---

## How to Use It
1. **Install**:
   ```bash
   uvx create-daca my-new-project
   cd my-new-project
   ```

2. **Set Up Environment**:
   ```bash
   echo "GEMINI_API_KEY=your-api-key" > chat_service/.env
   echo "GEMINI_API_KEY=your-api-key" > agent_memory_service/.env
   ```

3. **Run Locally**:
   - Initialize Dapr (`dapr init`) and ensure Redis is at `localhost:6379`.
   - Memory Agent:
     ```bash
     cd agent_memory_service
     uv venv
     source .venv/bin/activate
     uv sync
     dapr run --app-id agent-memory-service --app-port 8001 --dapr-http-port 3501 --resources-path ../components -- uv run uvicorn main:app --host 0.0.0.0 --port 8001 --reload
     ```
   - Chat Agent (new terminal):
     ```bash
     cd chat_service
     uv venv
     source .venv/bin/activate
     uv sync
     dapr run --app-id chat-service --app-port 8010 --dapr-http-port 3500 --resources-path ../components -- uv run uvicorn main:app --host 0.0.0.0 --port 8010 --reload
     ```

4. **Test**:
   - Initialize memory:
     ```bash
     curl -X POST http://localhost:8001/memories/junaid/initialize -H "Content-Type: application/json" -d '{"name": "Junaid", "preferred_style": "formal", "user_summary": "Junaid is a new user."}'
     ```
   - Chat:
     ```bash
     curl -X POST http://localhost:8010/chat/ -H "Content-Type: application/json" -d '{"user_id": "junaid", "text": "Hello"}'
     ```

5. **Try Swagger Docs**
In browser open
- Chat Agent: http://localhost:8010
- Memory Agent: http://localhost:80001

6. **Deploy**: Update Dapr components (e.g., use a cloud broker) and deploy to your environment.

---

## Core Breakdown & Code Explanation
This template includes two agents and Dapr components, with code designed for agentic collaboration:

### Chat Agent (`chat_service/`)
- **Role**: Engages users, publishes events to coordinate with the Memory Agent.
- **Key Code** (`main.py`):
  ```python
  async def publish_conversation_event(user_id: str, session_id: str, user_text: str, reply_text: str, dapr_port: int = 3500):
      dapr_url = f"http://localhost:{dapr_port}/v1.0/publish/pubsub/conversations"
      event_data = {
          "user_id": user_id, "session_id": session_id, "event_type": "ConversationUpdated",
          "user_message": user_text, "assistant_reply": reply_text
      }
      async with httpx.AsyncClient() as client:
          response = await client.post(dapr_url, json=event_data)
          response.raise_for_status()

  @app.post("/chat/", response_model=Response)
  async def chat(message: Message):
      chat_agent = Agent(name="ChatAgent", instructions="...", tools=[get_current_time], model=model)
      result = await Runner.run(chat_agent, input=message.text, run_config=config)
      await publish_conversation_event(message.user_id, session_id, message.text, result.final_output)
      return Response(user_id=message.user_id, reply=result.final_output, metadata=Metadata(session_id=session_id))
  ```
  - **What It Does**: Uses OpenAI Agents SDK to process input, publishes “ConversationUpdated” events via Dapr Pub/Sub for asynchronous coordination.

- **Models** (`models.py`):
  ```python
  class Message(BaseModel):
      user_id: str
      text: str
      metadata: Metadata | None = None
  class Response(BaseModel):
      user_id: str
      reply: str
      metadata: Metadata
  ```
  - **Purpose**: Defines data structures for chat input/output.

- **Tests** (`test_main.py`): Includes `pytest` mocks to verify event publishing and responses.

### Memory Agent (`agent_memory_service/`)
- **Role**: Listens to events, updates history, and generates dynamic metadata.
- **Key Code** (`main.py`):
  ```python
  async def generate_user_summary(user_id: str, history: list[dict]) -> str:
      summary_agent = Agent(name="SummaryAgent", instructions="Generate a concise summary...", model=model)
      history_text = "\n".join([f"{entry['role']}: {entry['content']}" for entry in history[-5:]])
      result = await Runner.run(summary_agent, input=history_text, run_config=config)
      return result.final_output

  @app.post("/conversations")
  async def handle_conversation_updated(event: dict):
      event_data = event.get("data", {})
      if event_data.get("event_type") == "ConversationUpdated":
          history = await get_conversation_history(event_data["session_id"])
          history.extend([{"role": "user", "content": event_data["user_message"]}, {"role": "assistant", "content": event_data["assistant_reply"]}])
          await set_conversation_history(event_data["session_id"], history)
          metadata = await get_user_metadata(event_data["user_id"])
          metadata["user_summary"] = await generate_user_summary(event_data["user_id"], history)
          await set_user_metadata(event_data["user_id"], metadata)
      return {"status": "SUCCESS"}
  ```
  - **What It Does**: Subscribes to `conversations` topic, updates state in Dapr’s store, and uses an LLM to enrich metadata.

- **Models** (`models.py`):
  ```python
  class UserMetadata(BaseModel):
      name: str
      preferred_style: str
      user_summary: str
  ```
  - **Purpose**: Structures memory data for persistence and retrieval.

- **Tests** (`test_main.py`): Verifies event handling, state updates, and summary generation.

### Dapr Components (`components/`)
- **Files**:
  - `pubsub.yaml`: Configures Redis Pub/Sub for event-driven communication.
    ```yaml
    apiVersion: dapr.io/v1alpha1
    kind: Component
    metadata:
      name: pubsub
    spec:
      type: pubsub.redis
      version: v1
      metadata:
      - name: redisHost
        value: localhost:6379
    ```
  - `statestore.yaml`: Configures Redis state store for persistent memory.
    ```yaml
    apiVersion: dapr.io/v1alpha1
    kind: Component
    metadata:
      name: statestore
    spec:
      type: state.redis
      version: v1
      metadata:
      - name: redisHost
        value: localhost:6379
    ```
  - `subscriptions.yaml`: Routes `conversations` topic to `/conversations` endpoint.
    ```yaml
    apiVersion: dapr.io/v1alpha1
    kind: Subscription
    metadata:
      name: conversation-subscription
    spec:
      pubsubname: pubsub
      topic: conversations
      route: /conversations
    ```
- **Purpose**: Provides the distributed runtime foundation for agent collaboration and state management.

---

## Why It’s an Agent-Serving Template
- **Develop + Deploy**: Code supports local development and distributed deployment with Dapr.
- **Distributed Runtime**: Dapr’s Pub/Sub and state management ensure agent resilience and scalability.
- **Agentic Design**: Chat and Memory Agents collaborate autonomously via events.
- **Flexible Engine**: Built with OpenAI Agents SDK, adaptable to LangGraph, CrewAI, or custom Python.
- **Cloud Foundation**: Ready for scaling agentic systems in distributed environments.
- **Educational**: Learn agentic principles through practical, deployable code.

---

## For Learning More
Explore the **Dapr Agentic Cloud Ascent (DACA)** series for a deeper dive:
- [DACA Series](https://github.com/panaversity/learn-agentic-ai/tree/main/01_openai_agents/17_daca_local_dev)

---

## Requirements
- Dapr CLI v1.15+ (`dapr init`)
- Docker (Redis)
- Python 3.12+ (3.13 compatible)
- UV
- Gemini API Key

---

## Why Use This?
- **Agent-First**: Ready-made agents for development and deployment.
- **Distributed**: Dapr runtime for scalability and resilience.
- **Flexible**: Any agent engine, any environment.
- **Learn**: Explore agentic systems hands-on.

Start your agentic journey with `uvx create-daca`!
