import sys
from pathlib import Path

import nest_asyncio

sys.path.append(str(Path(__file__).resolve().parents[1]))

nest_asyncio.apply()
from app.ai.decide import decide

question = "Panel 4 of my HP-S3 is cracked. Order 112-4839201-5528341"
decision = decide(question)
print(decision.model_dump_json(indent=2))


question2 = "I want my money back, this is ridiculous"
decision2 = decide(question)
print(decision2.model_dump_json(indent=2))