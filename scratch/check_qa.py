with open('scratch/exp11.log', 'r', encoding='utf-16') as f:
    text = f.read().replace('\n', '')

import re
print(f"QAAgent string: {'QAAgent' in text}")

qa_starts = re.findall(r'QAAgent starting', text)
print(f"QA started: {len(qa_starts)}")
