import logging
from fastapi import APIRouter, Depends
from backend.server.utils import get_user_id
from .models import SimulationApiResponse, SimulationRequest
from backend.blocks.intone.chromium_orchestration import ChromiumOrchestrationBlock,OrchestrationInteractionPrompt
from prisma.enums import AgentExecutionStatus, APIKeyPermission
from backend.server.external.middleware import require_permission
from backend.data.api_key import APIKey

logger = logging.getLogger(__name__)

IntoneRouter = APIRouter()


@IntoneRouter.post("/chromeauto/simulate", 
                   tags=["intone"],
                   response_model=SimulationApiResponse,
                   dependencies=[Depends(require_permission(APIKeyPermission.EXECUTE_GRAPH))]
                   )
def chromeauto_simulate(
    request: SimulationRequest, 
    api_key: APIKey = Depends(require_permission(APIKeyPermission.EXECUTE_BLOCK))
) -> SimulationApiResponse:
    """
   
    """
    user_id=api_key.user_id
    block1: ChromiumOrchestrationBlock = ChromiumOrchestrationBlock()
    input_data=ChromiumOrchestrationBlock.Input(
            refName="test2",url="https://timesheet.intonesolutions.com/view/admin/adminCal",
            instructions=
                [
                    OrchestrationInteractionPrompt(
                        instructions=request.previousInstructions[idx],
                        output=request.previousOutputs[idx]
                    )
                    for idx in range(len(request.previousInstructions))
                ],
            saveState=False,
            reloadStateOnStart=False
        )
    output=dict(block1.run(input_data,graph_exec_id=f"__graph_exec_sim_{user_id}",
                           graph_id=f"__graph_sim_{user_id}_{request.refName}",
                           user_id=user_id,
                           extSim=True,
                           domHtml=request.domHtml,
                           snapshotScreenshot=request.snapshotScreenshot,
                           simInstructions=request.instructions,
                           simCondition=request.condition))
    resp=SimulationApiResponse(
        code=output["output"],
        success=True
    )
    return resp
    
