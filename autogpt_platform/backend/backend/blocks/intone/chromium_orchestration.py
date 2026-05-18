from urllib.parse import quote
import os
from playwright.sync_api import sync_playwright,Page
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema,update_agent_persistvariabls
from backend.data.model import SchemaField
import time
import json
import re
from types import SimpleNamespace
import asyncio
import base64
import sys
import multiprocessing
from pydantic import BaseModel,SecretStr
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    NodeExecutionStats,
    SchemaField,
)
from typing import Any, Iterable, List, Literal, NamedTuple, Optional
from backend.integrations.providers import ProviderName
from backend.blocks.llm import llm_call,LlmModel
from backend.integrations.credentials_store import IntegrationCredentialsStore

class OrchestrationInteractionPrompt(BaseModel):
    condition: str=SchemaField(description="condition on the previous step output",default="")
    instructions: str=SchemaField(description="example: look for the user name field and password field then input the following data: username1 and password1 then click on (login) button",default="")
    output: Optional[str]=None # output of this step
# this class is created in runtime and populated from the above class + runtime fields below
class OrchestrationInteractionPromptExtended(OrchestrationInteractionPrompt):
    previous_step_output: Optional[str]=None # output from previous step 
    state_screenshot: Optional[str]=None # screenshot of the current browser state
    subject_screenshot: Optional[str]=None # presented to the LLM after post_waitForElementSelector is available
    post_wait_for_element_selector: Optional[str]=None # presented to the LLM after post_waitForElementSelector is available
    code: Optional[str]=None
    

class ChromiumOrchestrationBlock(Block):
    class Input(BlockSchema):
        refName: str=SchemaField(description="unique name within this agent. this can be used in other nodes to reference this browser's state.",default="",advanced=False)
        url: str = SchemaField(description="the url",default="")
        instructions: list[OrchestrationInteractionPrompt]=SchemaField(description="steps",default_factory=list,advanced=False)
        saveState:bool=SchemaField(description="save the state of this browser.",default=False,advanced=True)
        reloadStateOnStart:bool=SchemaField(description="reload the saved state (if available) when starting the browser.",default=False,advanced=True)

    class Output(BlockSchema):
        
        stdout_logs: str=SchemaField(description="std out",title="stdout logs")
        screenshot: str=SchemaField(description="browser screenshot")
        refName: str=SchemaField(description="unique name within this agent. this can be used in other nodes to reference this browser's state.")
        output:str=SchemaField(description="final output from the instructions")
    def wait_for_jquery_selector(self,page:any, sel:str, sel_timeout_sec:float):
        start = time.time()
        while True:
            found = page.evaluate(f'() => !!window.jQuery && jQuery("{sel}").length > 0')
            if found:
                return True
            if time.time() - start > sel_timeout_sec:
                return False
            time.sleep(0.2)

    def __init__(self):
        super().__init__(
            id="aabbccdd-0000-1111-2222-000000000004",
            description="This block uses chromium to grab content from the internet.",
            categories={BlockCategory.DATA},
            input_schema=ChromiumOrchestrationBlock.Input,
            output_schema=ChromiumOrchestrationBlock.Output,
        )

    def run(
        self, input_data: Input, **kwargs
    ) -> BlockOutput:
        try:
            debug:bool=os.getenv("debug")=="1"
            graph_exec_id=kwargs['graph_exec_id']
            graph_id=kwargs['graph_id']
            user_id=kwargs['user_id']
            variables=kwargs.get("variables") or []
            extSim=kwargs.get("extSim") or False
            if extSim:
                domHtml=kwargs.get("domHtml")
                snapshotScreenshot=kwargs.get("snapshotScreenshot")
                simInstructions=kwargs.get("simInstructions")
                simCondition=kwargs.get("simCondition")
            stdout_logs=""
            stateVarName=""
            extInsts=[]
            prevInstExt:OrchestrationInteractionPromptExtended=None
            if not extSim:    
                url = input_data.url
                refName=input_data.refName
                if not refName:
                    refName=url
                stateVarName=f"_state_{refName}"
                print(f"starting on url: {url}")
                stdout_logs +=f"starting on url: {url}\r\n"
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=not debug)
                    statevar= next((item for item in variables if item.VarName == stateVarName), None)
                    if input_data.reloadStateOnStart and statevar:
                        context = browser.new_context(storage_state=statevar.VarValue["state"]) 
                    else:
                        context = browser.new_context(
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                    "(KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
                            viewport={'width': 1280, 'height': 1000},
                            java_script_enabled=True,
                            ignore_https_errors=True,
                        )
                    print("browser created")
                    stdout_logs+="browser created\r\n"
                    page = context.new_page()
                    # 🧙 Inject stealth tricks
                    page.add_init_script("""
                        // Remove navigator.webdriver
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });

                        // Spoof plugins
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3]
                        });

                        // Spoof languages
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });
                    """)
                    # Step 1-2: Load the page and wait
                    print ("page created")
                    stdout_logs+="page created\r\n"
                    if input_data.reloadStateOnStart and statevar:
                        url=statevar.VarValue["url"]
                    page.goto(url, wait_until="load")

                    # Step 3: Wait additional sec
                    time.sleep(1.0)
                    print("adding jq injection")
                    stdout_logs+="adding jq injection\r\n"
                    # Step 4: Inject jQuery from CDN
                    jquery_url = "https://code.jquery.com/jquery-3.6.0.min.js"
                    has_jquery = page.evaluate("typeof window.jQuery !== 'undefined'")
                    if not has_jquery:
                        page.add_script_tag(url=jquery_url)

                    # Step 5: Wait for jQuery to be available
                    page.wait_for_function("() => window.jQuery !== undefined")
                    step=1
                    for instruction in input_data.instructions:
                        print(f"running instruction #{step}")
                        stdout_logs+=f"running instruction #{step}\r\n"
                        instExt:OrchestrationInteractionPromptExtended=OrchestrationInteractionPromptExtended(
                            **instruction.dict(),  # copies all fields from the base model
                            previous_step_output="",
                            state_screenshot="",
                            subject_screenshot="",
                            post_wait_for_element_selector="",
                            output=""
                        )
                        if prevInstExt:
                            instExt.previous_step_output=prevInstExt.output
                            instExt.state_screenshot=prevInstExt.state_screenshot
                        
                        instExt.instructions=self.replaceVar(extInsts,"instructions",instExt.instructions,step-1)
                        instExt.instructions=self.replaceVar(extInsts,"output",instExt.instructions,step-1)

                        output=self.runOneStep(user_id,instExt,page)
                        instExt.output=output
                    
                        prevInstExt=instExt
                        extInsts.append(instExt)
                        step+=1
                    savedState={
                        "url":url,
                        "state":context.storage_state(),
                        "extInsts": [item.dict() for item in extInsts] 
                    }
                    browser.close()
                if input_data.saveState:
                    jsonStr=json.dumps(savedState)
                    persistent_vars = [{"VarName":v.VarName,"VarValue":v.VarValue} for v in variables if v.Persistent]
                    state_var={"VarName":stateVarName,"VarValue":savedState}
                    var_map = {v["VarName"]: v for v in persistent_vars}
                    var_map[state_var["VarName"]] = state_var
                    persistent_vars = list(var_map.values())
                    persistent_vars = [SimpleNamespace(**item) for item in persistent_vars]
                    asyncio.run(update_agent_persistvariabls(graph_id=graph_id,variables=persistent_vars))
            else:
                step=1
                for instruction in input_data.instructions:
                    instExt:OrchestrationInteractionPromptExtended=OrchestrationInteractionPromptExtended(
                        **instruction.dict(),  # copies all fields from the base model
                        previous_step_output="",
                        state_screenshot="",
                        subject_screenshot="",
                        post_wait_for_element_selector="",
                    )
                    if prevInstExt:
                        instExt.previous_step_output=prevInstExt.output
                        instExt.state_screenshot=prevInstExt.state_screenshot
                    
                    instExt.instructions=self.replaceVar(extInsts,"instructions",instExt.instructions,step-1)
                    instExt.instructions=self.replaceVar(extInsts,"output",instExt.instructions,step-1)
                
                instExt=OrchestrationInteractionPromptExtended(
                    instructions=simInstructions,
                    condition=simCondition,
                    output="",
                    previous_step_output="",
                    state_screenshot="",
                    subject_screenshot="",
                    post_wait_for_element_selector="",
                )
                extInsts.append(instExt)
                prevInstExt=instExt
                cmd=self.generateCmd(simInstructions)
                output=self.executeAICmd(user_id,cmd,files={"dom.html":domHtml})
                prevInstExt.output=output
                
            
            yield "stdout_logs",stdout_logs
            yield "screenshot",prevInstExt.state_screenshot
            yield "refName",stateVarName
            yield "output",prevInstExt.output
        except Exception as e:
            print(f"Intone Chromium Grab block: An error occurred: {e}")
    def runOneStep (self,userid:str,instruction:OrchestrationInteractionPromptExtended,page:Page)->Any:
        if instruction.condition:
            cmd=f"No verbose. Be exact and brief. Answer in only one word: true or false. \r\n" + \
                f"given output={instruction.previous_step_output}\r\n check if {instruction.condition}"
            v=self.executeAICmd(cmd,None)
            if v.lower()=="false":
                instruction.output=instruction.previous_step_output
                return instruction
            
        page.evaluate(f'() =>window.scrollTo(0, document.body.scrollHeight);')
        page.evaluate(f'() =>window.scrollTo(0, 0);')
        output=""
        if instruction.instructions:
            screenshot_bytes = page.screenshot()
            instruction.subject_screenshot="data:image/png;base64," + base64.b64encode(screenshot_bytes).decode()
            
            dom= page.evaluate("document.body.outerHTML")
            cmd=self.generateCmd(instruction.instructions)
            print(f"cmd:{cmd}\n")
            scope={"page":page,"output":None}
            for i in range(0,3,1):
                try:
                    code=self.executeAICmd(userid=userid,command=cmd,files={"screenshot.png":instruction.subject_screenshot,"dom.html":dom})
                    instruction.code=code
                    # now we need to execute this code on the page
                    print(code)
                    exec(code,scope)
                    print('executed\n')
                    break
                except Exception as e:
                    print (e)

            screenshot_bytes = page.screenshot()
            instruction.state_screenshot="data:image/png;base64," + base64.b64encode(screenshot_bytes).decode()
            output=scope["output"] or ""
        return output
    def executeAICmd(self,userid:str,command:str,files:dict[str,str]):
        credstore=IntegrationCredentialsStore()
        creds=credstore.get_all_creds(userid)
        OPENAICREDENTIALS=next(c for c in creds if c.provider == "openai")
        if not OPENAICREDENTIALS:
            return ""
        if not files:
            files={}
        prompt=[{"role":"user","content":command}]
        resp=llm_call(credentials=OPENAICREDENTIALS,llm_model=LlmModel.GPT4O,files=files,prompt=prompt,json_format=False,max_tokens=None)
        code= resp.raw_response.content
        matches = re.findall(r"```python\s*(.*?)```", code, re.DOTALL)
        code=matches[0].strip()
        return code
    def replaceVar (self,list:list,name:str,text:str,currentIndex:int):
        for i, val in enumerate(list):
            text = text.replace(f"{{{name}[{i}]}}", getattr(val,name,""))
        for i in range(currentIndex-1, -1, -1):
            j=i-currentIndex
            val=list[i]
            text = text.replace(f"{{{name}[{j}]}}", getattr(val,name,""))
        return text

    def generateCmd(self,instructions:str):
        # cmd=    "Answer without explanation, no verbose, only pure code. You are a python developer expert in playwright and instrumentation. the code you will generate is global code i.e. no function, no function name, just code that I can embed inside my own function. my function is not awaitable so if there is code that requires await, you need to wrap it with asyncio. Also assume that the browser is already instantiated and running and the page has been initialized and navigated to the desired url. " + \
        #         "\r\n you are not to interact directly with anything. you only need to generate instrumentation python code to instrument playwright to perform the instructions below.\r\n" + \
        #         " Assume the page can be referenced by the variable (page).\r\n" + \
        #         " you need to analyze with highest precision the attached image which is screenshot of the browser. This screenshot is from the browser with viewport of 1280 x 2800. and since the uploaded image may be resized to optimize your performance, you have to keep that under consideration. \r\n" + \
        #         " when instructed to find an element, you must only use the screenshot and do not use any other methods such as text-based selector or finding elements by text or class or id. only coordinates from the screenshot. " + \
        #         " when finding the coordinates of an element, you first need to calculate the ratios of rx, ry based on the size of the image (width and hieight) in relation to the size of the original screenshot (1280 x 2800). " + \
        #         " you must then extract the exact (x, y, width, height) pixel coordinates of that element on the uploaded image then use the rx, ry to determine the correct coordinates on the original image. \r\n" + \
        #         " the detailed steps to find the coordinates of an element should be added to the code as comments. " + \
        #         " when instructed to interact with the browser, you will generate code that simulates the interactions by generating mouse events and keyboard events in conjunctions \r\n" + \
        #         " with the coordinates of the original browser screenshot. for example: if instructed to find an input field and input some data, \r\n" + \
        #         " once you found it on the screenshot, calculate the corresponding coordinates of the input field on the browser \r\n" + \
        #         " then write code that generate mouse click to the coordinates of the input field (with some margin so that the mouse event is inside the field) \r\n" + \
        #         " then write code that generates series of keyboard events to be sent to that field which corresponds to the input data.\r\n"
        # cmd=    "Answer without explanation, no verbose, only pure code. You are a python developer expert in playwright and instrumentation. " + \
        #         " the code you will generate is global code i.e. no function, no function name, just code that I can embed inside my own function. " + \
        #         " my function is not awaitable so if there is code that requires await, you need to wrap it with asyncio. " + \
        #         " Also assume that the browser is already instantiated and running and the page has been initialized and navigated to the desired url. " + \
        #         " you are not to interact directly with anything. you only need to generate instrumentation python code to instrument playwright " + \
        #         " to perform the instructions below.\r\n" + \
        #         " Assume the page can be referenced by the variable (page).\r\n" + \
        #         " First thing, in code comment show the exact width and height of the attached image without showing me how you got it. call them: imgw, and imgh. \r\n" + \
        #         " second, write code that calculates rw=imgw/1280 and rh=imgh/2800. \r\n" + \
        #         " then I will ask you to perform a list of tasks below. to find an element, find it its exact coordinates on the screen using your intelligence to visuall identify the element (no code) and do not dom selectors. " + \
        #         " the x,y of the element must be exact so no examples. " + \
        #         " once you found the elemnt, assume its coordinates are x,y. then calculate the original x,y (ox=x/rw and oy=y/oh). " + \
        #         " \r\n"
        cmd=    "Answer without explanation, no verbose, only pure code. You are a python developer expert in playwright and instrumentation. " + \
                    " the code you will generate is global code i.e. no function, no function name, just code that I can embed inside my own function. " + \
                    " your code must be accurate and meticulously written and no room for mistakes. you must think about the approach of the code before you code it. " + \
                    " avoid infinite loops such as (while true). " +\
                    " do not and never use async functions or asyncio or await. \r\n" + \
                    " Also assume that the browser is already instantiated and running and the page has been initialized and navigated to the desired url. " + \
                    " you are not to interact directly with anything. you only need to generate instrumentation python code to instrument playwright " + \
                    " to perform the instructions below.\r\n" + \
                    " Assume the page can be referenced by the variable (page).\r\n" + \
                    " To find and identify elements, you need to extract and analyze the attached DOM of the page. use the attached screenshot image for visual cues.  " + \
                    " Another thing: the page is injected with jQuery in case you need to use it.\r\n" + \
                    " Always ensure the code you generate is correct and can be executed without mistakes. \r\n" +\
                    " if any instruction asks to return a value or output a value, always set a single global variable (output) to that value.\r\n"+\
                    "" # " if you use page.evaluate(), you must use try/catch block for the expression you are going to evaluate.\r\n" 
        cmd=cmd + f" The following are the instructions I need you to simulate: \r\n\r\n {instructions}"
        return cmd
