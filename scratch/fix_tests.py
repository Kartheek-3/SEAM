import re

with open('tests/agents/supervisor/test_supervisor_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all occurrences of 'self.call_count += 1' inside InspectingDeliveryMock
content = re.sub(r'(\s+)self\.call_count \+= 1\n(\s+self\.captured_inputs\.append\(input\))', r'\1\2', content)
content = re.sub(r'(\s+)self\.call_count \+= 1\n(\s+dep_outputs = input\.context\.get\("dependency_outputs", \[\]\))', r'\1\2', content)

with open('tests/agents/supervisor/test_supervisor_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)
