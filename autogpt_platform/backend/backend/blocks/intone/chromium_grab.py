from urllib.parse import quote

from playwright.sync_api import sync_playwright
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
import time

class ChromiumContentGrab(Block):
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
        contentText: str = SchemaField(
            description="The content of the page in text (striped from any html)"
        )
        contentHtml: str = SchemaField(
            description="The content of the page in html"
        )
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
            input_schema=ChromiumContentGrab.Input,
            output_schema=ChromiumContentGrab.Output,
        )

    def run(
        self, input_data: Input, **kwargs
    ) -> BlockOutput:
        
        url = input_data.url
        sel=input_data.selectorToWaitFor
        sel_timeout=input_data.maxTimeInSec
        result_sel=input_data.resultSelector
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Step 1-2: Load the page and wait
            page.goto(url, wait_until="load")

            # Step 3: Wait additional sec
            time.sleep(1.0)

            # Step 4: Inject jQuery from CDN
            jquery_url = "https://code.jquery.com/jquery-3.6.0.min.js"
            page.add_script_tag(url=jquery_url)

            # Step 5: Wait for jQuery to be available
            page.wait_for_function("() => window.jQuery !== undefined")

            # Step 6: Poll for `sel` using jQuery until found or timeout
            if not self.wait_for_jquery_selector(page=page,sel=sel,sel_timeout_sec=sel_timeout):
                browser.close()
                return None

            # Step 7: Query `resultSel` and return its text if found
            text = page.evaluate(f'() => jQuery("{result_sel}").first().text() || null')
            html=page.evaluate(f'() => jQuery("{result_sel}").first().html() || null')
            browser.close()
            yield "contentText", text
            yield "contentHtml", html

# for testing
# if __name__ == "__main__":
    
#     url = "https://www.kayak.ae/flights/CAI-YYZ/2025-06-28/2025-10-10/business/2adults?ucs=1oezqmi&sort=price_a&fs=stops=-2&attempt=1&lastms=1743751829186"
#     sel = ".e_0j-results-count"
#     sel_timeout = 10
#     result_sel = ".ev1_-results-list"
    
#     scraper = ChromiumContentGrab()
#     input_args=ChromiumContentGrab.Input(url=url,selectorToWaitFor=sel,maxTimeInSec=sel_timeout,resultSelector=result_sel)
#     result = scraper.run(input_data=input_args)
#     print("Result:", list(result))
#     input("Press any key to close...")
