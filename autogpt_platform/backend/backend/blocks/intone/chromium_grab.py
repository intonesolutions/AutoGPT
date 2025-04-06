from urllib.parse import quote

from playwright.sync_api import sync_playwright
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
import time

class ChromiumContentGrabBlock(Block):
    class Input(BlockSchema):
        url: str = SchemaField(
            description="the url"
        )
        selectorToWaitFor: str = SchemaField(
            description="The selector to wait for when the page is loaded"
        )
        maxTimeInSec: int=SchemaField(description="max time to wait for the selector in seconds")
        resultSelector: str=SchemaField(description="the selector for the result content")

    class Output(BlockSchema):
        content_text: str = SchemaField(
            description="The content of the page in text (striped from any html)"
        )
        content_html: str = SchemaField(
            description="The content of the page in html"
        )
        stdout_logs: str=SchemaField(description="std out",title="stdout logs")
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
            stdout_logs=""
            url = input_data.url
            sel=input_data.selectorToWaitFor
            sel_timeout=input_data.maxTimeInSec
            result_sel=input_data.resultSelector
            print(f"starting on url: {url}")
            stdout_logs +=f"starting on url: {url}\r\n"
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                print("browser created")
                stdout_logs+="browser created\r\n"
                page = browser.new_page()
                # Step 1-2: Load the page and wait
                print ("page created")
                stdout_logs+="page created\r\n"
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
                    browser.close()
                    return None

                # Step 7: Query `resultSel` and return its text if found
                print("eval selection jq")
                text = page.evaluate(f'() => jQuery("{result_sel}").first().text() || null')
                stdout_logs+=f"eval text: {text}"
                html=page.evaluate(f'() => jQuery("{result_sel}").first().html() || null')
                browser.close()
                yield "stdout_logs",stdout_logs
                yield "content_text", text
                yield "content_html", html
        except Exception as e:
            print(f"Intone Chromium Grab block: An error occurred: {e}")

# for testing
# if __name__ == "__main__":
    
#     url = "https://www.kayak.ae/flights/CAI-YYZ/2025-06-28/2025-10-10/business/2adults?ucs=1oezqmi&sort=price_a&fs=stops=-2&attempt=1&lastms=1743751829186"
#     sel = ".e_0j-results-count"
#     sel_timeout = 10
#     result_sel = ".ev1_-results-list"
    
#     scraper = ChromiumContentGrabBlock()
#     input_args=ChromiumContentGrabBlock.Input(url=url,selectorToWaitFor=sel,maxTimeInSec=sel_timeout,resultSelector=result_sel)
#     result = scraper.run(input_data=input_args)
#     print("Result:", list(result))
#     input("Press any key to close...")
