from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from bpmn_assistant.api.requests import (
    BpmnToJsonRequest,
    DetermineIntentRequest,
    ModifyBpmnRequest,
    ConversationalRequest,
)
from bpmn_assistant.config import logger
from bpmn_assistant.services import (
    BpmnModelingService,
    determine_intent,
    BpmnXmlGenerator,
    ConversationalService,
    BpmnJsonGenerator,
)
from bpmn_assistant.utils import (
    get_llm_facade,
    get_available_providers,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bpmn_modeling_service = BpmnModelingService()
bpmn_xml_generator = BpmnXmlGenerator()


@app.post("/bpmn_to_json")
def _bpmn_to_json(request: BpmnToJsonRequest) -> JSONResponse:
    """
    Convert the BPMN XML to its JSON representation
    """
    try:
        bpmn_json_generator = BpmnJsonGenerator()
        result = bpmn_json_generator.create_bpmn_json(request.bpmn_xml)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/available_providers")
def _available_providers() -> JSONResponse:
    """
    Get the available LLM providers
    """
    providers = get_available_providers()
    return JSONResponse(content=providers)


@app.post("/determine_intent")
async def _determine_intent(request: DetermineIntentRequest) -> JSONResponse:
    """
    Determine the intent of the user query
    """
    try:
        llm_facade = get_llm_facade(request.model)
        intent = determine_intent(llm_facade, request.message_history)
        return JSONResponse(content=intent)
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/modify")
async def _modify(request: ModifyBpmnRequest) -> JSONResponse:
    """
    Modify the BPMN process based on the user query. If the request does not contain a BPMN JSON,
    then create a new BPMN process. Otherwise, edit the existing BPMN process.
    """
    try:
        llm_facade = get_llm_facade(request.model)

        if request.process:
            logger.info("Editing the BPMN process...")
            process = bpmn_modeling_service.edit_bpmn(
                llm_facade, request.process, request.message_history
            )
        else:
            logger.info("Creating a new BPMN process...")
            process = bpmn_modeling_service.create_bpmn(
                llm_facade, request.message_history
            )

        bpmn_xml_string = bpmn_xml_generator.create_bpmn_xml(process)

        return JSONResponse(content={"bpmn_xml": bpmn_xml_string, "bpmn_json": process})

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/talk")
async def _talk(request: ConversationalRequest) -> StreamingResponse:
    conversational_service = ConversationalService(request.model)

    if request.needs_to_be_final_comment:
        response_generator = conversational_service.make_final_comment(
            request.message_history, request.process
        )
    else:
        response_generator = conversational_service.respond_to_query(
            request.message_history, request.process
        )

    return StreamingResponse(response_generator)
