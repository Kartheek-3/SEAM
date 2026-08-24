from agents.coding.agent import CodingAgent
from backend.schemas.agent_io import AgentInput
from backend.schemas.enums import TaskType

input_data = AgentInput(
    task_id='123',
    task_type=TaskType.CODING,
    context={
        'dependency_outputs': [
            {'id': 'art-1', 'name': 'foo.py', 'type': 'code', 'language': 'python', 'content': 'print("hello")'*1000}
        ]
    },
    instructions='Do it',
    dependencies=[]
)

agent = CodingAgent(llm_client=None)
prompt = agent._format_prompt(input_data)
print(f'Length of prompt: {len(prompt)}')
import re
match = re.search(r'Dependency Outputs.*?:(.*?)Domain Knowledge', prompt, re.DOTALL)
if match:
    print(f"Dependency context block size: {len(match.group(1))}")
    print(match.group(1).strip()[:200])
else:
    print("No block found")
