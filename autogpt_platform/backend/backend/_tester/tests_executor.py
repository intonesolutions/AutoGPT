from backend.util.process import AppProcess
import time
from backend.blocks.intone.chromium_orchestration import ChromiumOrchestrationBlock,OrchestrationInteractionPrompt

class TestsExecutor(AppProcess):
    def run(self):
        print ('=========> Tests executor is running...............')
        time.sleep(2)
        self.test_chromeOrch()

    def cleanup(self):
        return super().cleanup()
    
    def test_chromeOrch(self):
        block1: ChromiumOrchestrationBlock = ChromiumOrchestrationBlock()

        # input_data=ChromiumOrchestrationBlock.Input(
        #     refName="test1",url="https://www.sisystems.com/",
        #     instructions=[
        #         OrchestrationInteractionPrompt(
        #             condition="",
        #             instructions="find a link with the exact caption \"candidate login\" then click on it then pause for 5 seconds."
        #         ),
        #         OrchestrationInteractionPrompt(
        #             condition="",
        #             instructions="enter (tshazli@live.com) in the email input box and (Pepper#25) in the password input box then click on (sign in) then wait 10 secs."
        #         )
        #     ],
        #     saveState=True,
        #     reloadStateOnStart=True
        # )
        input_data=ChromiumOrchestrationBlock.Input(
            refName="test2",url="https://timesheet.intonesolutions.com/view/admin/adminCal",
            instructions=[
                OrchestrationInteractionPrompt(
                    condition="",
                    instructions="from the location dropdown, select (eat nabati - kensigton) then call its onchange event and wait 3 secs."
                ),
                OrchestrationInteractionPrompt(
                    condition="",
                    instructions="read the date of Mon at the top of the table to know if we need to go previous or next. using the buttons with (<<) for previous week and (>>) for next week, select the week that starts with Mon Jun 09. when you press the button, you have to wait 3 secs for the page to refresh."
                )
                ,
                OrchestrationInteractionPrompt(
                    condition="",
                    instructions="iterate through all the rows which each denotes an employee then output each name with their hours like this: emp1:5,emp2:3,..."
                )
                ,
                OrchestrationInteractionPrompt(
                    condition="",
                    instructions="move to the next week using the button (>>) then wait for 3 secs and then {instructions[-1]}"
                )
                ,
                OrchestrationInteractionPrompt(
                    condition="",
                    instructions="merge these 2 lists which is a list of employee:hours by adding the hours for the same employee and output the result:\n{output[-2]}\n{output[-1]}\n"
                )
            ],
            saveState=True,
            reloadStateOnStart=True
        )
        output=dict(block1.run(input_data,graph_exec_id="__graph_exec_test_01",graph_id="__graph_test_01",user_id="1dd39d21-b407-4670-a124-e41e9929489b"))
        print(output["output"])
        print("===================")



