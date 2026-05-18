from urllib.parse import quote

from playwright.sync_api import sync_playwright
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema,update_agent_persistvariabls
from backend.data.model import SchemaField
import time
import json
from types import SimpleNamespace
import asyncio
class ChromiumContentGrabBlock(Block):
    class Input(BlockSchema):
        refName: str=SchemaField(description="unique name within this agent. this can be used in other nodes to reference this browser's state.",default="",advanced=False)
        url: str = SchemaField(description="the url")
        selectorToWaitFor: str = SchemaField(description="The selector to wait for when the page is loaded")
        maxTimeInSec: int=SchemaField(description="max time to wait for the selector in seconds")
        filterScript: str=SchemaField(description="js script to execute right before grabbing the content. use $ for jQuery",default="")
        resultSelector: str=SchemaField(description="the selector for the result content")
        saveState:bool=SchemaField(description="save the state of this browser.",default=False,advanced=True)
        reloadStateOnStart:bool=SchemaField(description="reload the saved state (if available) when starting the browser.",default=False,advanced=True)

    class Output(BlockSchema):
        content_text: str = SchemaField(description="The content of the page in text (striped from any html)")
        content_html: str = SchemaField(description="The content of the page in html")
        stdout_logs: str=SchemaField(description="std out",title="stdout logs")
        screenshot: str=SchemaField(description="browser screenshot")
        refName: str=SchemaField(description="unique name within this agent. this can be used in other nodes to reference this browser's state.")
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
            id="aabbccdd-0000-1111-2222-000000000001",
            description="This block uses chromium to grab content from the internet.",
            categories={BlockCategory.DATA},
            input_schema=ChromiumContentGrabBlock.Input,
            output_schema=ChromiumContentGrabBlock.Output,
        )

    def run(
        self, input_data: Input, **kwargs
    ) -> BlockOutput:
        try:
            graph_exec_id=kwargs['graph_exec_id']
            graph_id=kwargs['graph_id']
            user_id=kwargs['user_id']
            variables=kwargs.get("variables") or []
            url = input_data.url
            refName=input_data.refName
            if not refName:
                refName=url
            stateVarName=f"_state_{refName}"
            stdout_logs=""
            sel=input_data.selectorToWaitFor
            sel_timeout=input_data.maxTimeInSec
            result_sel=input_data.resultSelector
            print(f"starting on url: {url}")
            stdout_logs +=f"starting on url: {url}\r\n"
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                statevar= next((item for item in variables if item.VarName == stateVarName), None)
                if input_data.reloadStateOnStart and statevar:
                   context = browser.new_context(storage_state=statevar.VarValue["state"]) 
                else:
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                "(KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
                        viewport={'width': 1280, 'height': 2800},
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
                page.add_script_tag(url=jquery_url)

                # Step 5: Wait for jQuery to be available
                page.wait_for_function("() => window.jQuery !== undefined")

                # Step 6: Poll for `sel` using jQuery until found or timeout
                print("running selection jq")
                stdout_logs+="running selection jq\r\n"
                if not self.wait_for_jquery_selector(page=page,sel=sel,sel_timeout_sec=sel_timeout):
                    print("waiting expired")
                    #browser.close()
                    #return None

                # Step 7: Query `resultSel` and return its text if found
                print("eval selection jq")
                page.evaluate(f'() =>window.scrollTo(0, document.body.scrollHeight);')
                page.evaluate(f'() =>window.scrollTo(0, 0);')
                if input_data.filterScript:
                    scrpt=input_data.filterScript.replace("$","jQuery")
                    page.evaluate(f'() => {scrpt}')
                text = page.evaluate(f'() => jQuery("{result_sel}").first().text() || ""')
                stdout_logs+=f"eval text: {text}"
                html=page.evaluate(f'() => jQuery("{result_sel}").first().html() || ""')
                screenshot_bytes = page.screenshot()
                import base64
                data_url = "data:image/png;base64," + base64.b64encode(screenshot_bytes).decode()
                savedState={
                    "url":url,
                    "state":context.storage_state()
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

            
            yield "stdout_logs",stdout_logs
            yield "content_text", text
            yield "content_html", html
            yield "screenshot",data_url
            yield "refName",stateVarName
        except Exception as e:
            print(f"Intone Chromium Grab block: An error occurred: {e}")

# for testing
if __name__ == "__main__":
    
    url = "https://www.kayak.ae/flights/CAI-YYZ/2025-06-28/2025-10-10/business/2adults?ucs=1oezqmi&sort=price_a&fs=stops=-2&attempt=1&lastms=1743751829186"
    sel = ".e_0j-results-count"
    sel_timeout = 10
    result_sel = ".ev1_-results-list"
    
    scraper = ChromiumContentGrabBlock()
    input_args=ChromiumContentGrabBlock.Input(url=url,selectorToWaitFor=sel,maxTimeInSec=sel_timeout,resultSelector=result_sel)
    result = scraper.run(input_data=input_args)
    print("Result:", list(result))
    input("Press any key to close...")
