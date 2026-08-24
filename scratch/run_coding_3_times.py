import asyncio
import time
from agents.coding.agent import CodingAgent
from backend.schemas.agent_io import AgentInput
from backend.schemas.enums import TaskType
from backend.llm.ollama_client import OllamaClient

async def run_three_times():
    client = OllamaClient(model_name="llama3.1")
    agent = CodingAgent(llm_client=client)

    input_data = AgentInput(
        task_id='123',
        task_type=TaskType.CODING,
        context={
            'dependency_outputs': [
                {
                    'id': 'art-1', 
                    'name': 'foo.py', 
                    'type': 'code', 
                    'language': 'python', 
                    'content': 'print("hello")'*1000
                }
            ]
        },
        instructions='Write a simple python script that prints hello world inside src/hello.py',
        dependencies=[]
    )

    for i in range(1, 4):
        print(f"\n--- Execution {i} ---")
        prompt = agent._format_prompt(input_data)
        print(f"Total prompt size: {len(prompt)}")
        start = time.time()
        output = await agent.execute(input_data)
        duration = time.time() - start
        
        print(f"Duration: {duration:.2f}s")
        print(f"Success: {output.status.value}")
        print(f"Files generated: {output.result.get('files_generated', 0)}")
        print(f"Feedback: {output.feedback}")

if __name__ == "__main__":
    asyncio.run(run_three_times())
