from pydantic import BaseModel
from datetime import datetime
import json

class TestModel(BaseModel):
    d: datetime

model = TestModel(d=datetime.now())

# This will fail
try:
    print(json.dumps(model.model_dump()))
except Exception as e:
    print(f"Failed standard: {e}")

# This should succeed
try:
    print(json.dumps(model.model_dump(mode='json')))
    print("Success mode=json")
except Exception as e:
    print(f"Failed mode=json: {e}")
