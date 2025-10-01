from typing import Any, Dict, Optional

from pydantic import BaseModel

class SimulationRequest(BaseModel):
    refName: str
    domHtml: str
    snapshotScreenshot: str
    instructions: str
    condition: str
    previousOutputs: list[str]
    previousInstructions: list[str]

class SimulationApiResponse(BaseModel):
    code: str
    success: bool