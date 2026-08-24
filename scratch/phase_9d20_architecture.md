# Phase 9D.20 Architecture Inspection

## 1. Current LLM Call Path
1. `evaluation/runner.py` instantiates `raw_llm_client = OllamaClient(model_name=...)`.
2. It wraps it in a `TelemetryLLMClient`.
3. The client is passed via constructor to each agent (e.g., `CodingAgent(llm_client=llm_client, ...)`).
4. Agents call `await self.llm.generate_structured_output(...)` (or `generate_structured_response`).
5. `OllamaClient` configures a LangChain `Ollama` instance pointing to the hardcoded `settings.ollama_base_url` (usually `http://localhost:11434`) and handles Pydantic JSON parsing.

## 2. OllamaClient Responsibilities
- Initializing the LangChain `Ollama` model wrapper with temperature, timeout, and base URL.
- Formatting the system and user prompts with JSON schema instructions using `JsonOutputParser`.
- Executing the request (`chain.ainvoke`).
- Parsing the dict back into the strong Pydantic response model.
- Catching and standardizing exceptions (`ValidationError`, `TimeoutError` -> `LLMException`).

## 3. How agents currently obtain the LLM
Agents obtain the LLM via dependency injection in their `__init__` constructor. They expect any object conforming to the `LLMClient` protocol signature.

## 4. Whether agents can safely receive a worker/client without changing their public contracts
Yes. Because agents rely on the `LLMClient` protocol (duck typing), we can inject a `WorkerAwareOllamaClient` that implements `generate_structured_output` exactly like the original. The agents will remain entirely unaware of the underlying distributed worker pool.

## 5. Where a WorkerPool can be inserted with minimum architectural impact
The pool should be inserted behind a new adapter class (e.g., `WorkerAwareOllamaClient` in `backend/llm/worker_client.py` or similar). 
- When an agent calls `generate_structured_output`, the adapter requests a worker from the `WorkerPool`.
- The pool marks the worker `BUSY`.
- The adapter configures a localized LangChain `Ollama` call pointing to that specific worker's host/port.
- On success/failure, the adapter releases the worker back to the pool (`AVAILABLE`), unless there is a severe infrastructure failure (e.g., `TimeoutError`, `ConnectionError`), in which case the worker is marked `UNHEALTHY`.

## 6. Any concurrency limitations already present
Currently, the system blasts all concurrent supervisor tasks (e.g., QA tasks running in parallel) at a single `localhost:11434` endpoint. This causes connection resets and timeouts under load. The new `WorkerPool` will enforce concurrency limits equal to the number of configured active workers, blocking or erroring if no workers are available, thus preventing the 120+ DNS errors observed in Experiment #16.
