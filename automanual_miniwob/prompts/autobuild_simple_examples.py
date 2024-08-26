init_rules = {
'rule_0': {"rule": "If need to enter text in the input box, use 'click_and_type' method as shown in the example.", "type": "Useful Helper Method", "example": '''# Click the input box and type text.
def click_and_type(agent, input_id, text):
  inputbox_xpath = f"//*[@id='{input_id}']"
  agent.click_xpath(inputbox_xpath)
  agent.type(text)
''', "validation_record": "Helper method provided by User."}
}

builder_example = '''
Previously discovered rules: \{...\}
Current epoch's trajectory: \{
'epoch_0_interact_0': "obs_0: Your task is to Enter "Ronda" into the text field and press Submit.\n...(HTML)...", 
'epoch_0_interact_1': "Agent's analysis: ...\nAgent's code:```python
def click_and_type(agent, input_id, text):
  inputbox_xpath = f"//*[@id='{input_id}']"
  agent.click_xpath(inputbox_xpath)
  agent.type(text)

# [Step 1] Click the input box and type "Ronda"
click_and_type(agent, 'tt', "Ronda")

# [Step 2] Click the submit button
submit_button_xpath = "//button[@id='subbtn']"
agent.click_xpath(submit_button_xpath)
```

### Feedbacks ###
...(some feedbacks)...
obs_3: Act: agent.click_xpath("//button[@id='subbtn']"). Obs: Action done. The epoch is Done. Succeed: True."\}

### Outputs ###:
In this epoch, the agent complete the task of entering a text.

### Potential Rules:
1. #if success# *Success Process*: To submit text, Steps 1 is to click <input> textbox and type the target string. Steps 2 is to click "Submit" button. This success process hasn't been include in the scope of the existing 'Success Process' rule.
2. #if success and helper method exists# *Helper method*: The 'click_and_type' method is successfully used to click and type text. This helper method doesn't overlap with the existing 'Useful Helper Method' rule.
3. #if errors exist# *Corrected Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
4. #if failed# *Unresolved Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
#Other important rules:#
5. ... (whether the mechanism is related to the existing rule)

### Check Difference:
Potential Rule 1 addresses the entire success process. Potential Rule 2 targetes the 'click_and_type' method..... They target different phenomena.

### Check Existing Rules:
* rule_0: ...(is not related to this trajectory). 
* rule_1: ...(is conflicted or need updating).

### Code:
```python
rule_manager.write_rule(
rule = "If need to enter text in the input box, use 'click_and_type' method as shown in the example.",
type = "Useful Helper Method",
example = \'''# Click the input box and type text.
def click_and_type(agent, input_id, text):
  inputbox_xpath = "//*[@id=input_id]"
  agent.click_xpath(inputbox_xpath)
  agent.type(text)
\''',
validation_record = "The 'click_and_type' method shows it can successfully type text into the input box in epoch_0.")

rule_manager.write_rule(
rule = "If the task need to submit text, first click <input> textbox, type the target string, and then click \"Submit\" button.",
type = "Success Process",
example = \'''# For example, to Enter "Ronda" into the text field and Submit:
# [Step 1] Use 'click_and_type' method to click <input> textbox and type "Ronda".
# [Step 2] Click the Submit button.
\''',
validation_record = "This process adopts the method in 'rule_0' and is vaild by the success of epoch_0.")

rule_manager.stop_generating()
```
'''

worker_example = '''
Your task is to Enter "Ronda" into the text field and press Submit.
...(HTML)...
### Outputs ###

### Understanding of the observation: ...
### Rules to consider: ...
### Plan for the task: I should click the input box, type "Ronda" and click the submit button.
### Code:
```python
# [Step 1] Click the input box
inputbox_xpath = "//input[@id='tt']"
agent.click_xpath(inputbox_xpath)

# [Step 2] Type "Ronda" into the input box
agent.type("Ronda")

# [Step 3] Click the submit button
submit_button_xpath = "//button[@id='subbtn']"
agent.click_xpath(submit_button_xpath)
```

### Feedbacks ###
...(some feedbacks)...
obs_3: Act: agent.click_xpath("//button[@id='subbtn']"). Obs: Action done. The epoch is Done. Succeed: True.
'''.strip()
