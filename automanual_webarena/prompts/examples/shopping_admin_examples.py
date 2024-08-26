init_rules = {
'rule_0': {"rule": "If the task need to identify the top best-selling band within a period, first go the link 'Bestsellers' in 'REPORTS'. Next, filter with the proper period and calculate the quantity for each band.", "type": "Success Process", "example": '''# For example, to answer the top-1 best-selling band in Quarter 1 2022:
# [Step 1] Click link '\\ue60a REPORTS'.
# [Step 2] Click link 'Bestsellers' to filter the report.
# [Step 3] Click the 'Period' box and select the option 'Month'.
# [Step 4] Type the begining and the ending of the time zone.
# [Step 5] Click the button 'Show Report'
# [Step 6] Manually figure out the top-1 best-selling band
''', "validation_record": "Provided by User."},
'rule_1': {"rule": "To filter the selling report within a period, you can go to the link 'Bestsellers' in the '\\ue60a REPORTS'.", "type": "Special Mechanism", "example": '''
agent.click(126) # where [126] is link '\\ue60a REPORTS'
agent.click(602) # where [602] is link 'Bestsellers'
''', "validation_record": "Provided by User."},
'rule_2': {"rule": "It is important to set the filter correctly. For example, set 'Day' as 'Period' to display the report of a Quarter would be too long to view.", "type": "Special Mechanism", "example": '''
agent.click(1267, 'Month') # Swith the 'Period' option from 'Day' to 'Month'
''', "validation_record": "Provided by User."}
}

builder_example = '''
Previously discovered rules: \{...\}
Current epoch's trajectory: \{
'epoch_0_interact_0': "obs_0: What is the top-1 best-selling brand in Quarter 1 2022.\nOBSERVATION: ...", 'epoch_0_interact_1': "Agent's analysis: ...\nAgent's code: ```python
# Click the 'REPORTS' link
agent.click(126)
```
obs_1: Act: agent.click(126). Obs: click [126] where [126] is link '\\ue60a REPORTS'\nOBSERVATION: ...",
'epoch_0_interact_2': "Agent's analysis: ...\nAgent's code: ```python
# Click the 'Bestsellers' link
agent.click(602)
```
obs_2: Act: agent.click(602). Obs: click [602] where [602] is link 'Bestsellers'\nOBSERVATION: ...",
...
'epoch_0_interact_7': "Agent's analysis: ...\nAgent's code: ```python
# Manually count and stop with the answer
agent.stop("Sprite")
```
obs_7: Act: agent.stop("Sprite"). Obs: Action has been performed. This epoch is done. Succeed: True"\}

### Outputs ###:
In this epoch, the agent completes the task of answering the top best-selling band in Quarter 1 2022.
### Potential Rules:
1. #if success# *Success Process*: To identify the top best-selling product within a period, Steps 1 is to click the 'REPORTS' link and 'Bestsellers' link, Steps 2 is to select the period of 'Month', Steps 3 is to type the time zone into the filter, Steps 4 is to count the order quantity for each band. This success process hasn't been include in the scope of the existing 'Success Process' rule.
2. #if errors exist# *Corrected Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
3. #if failed# *Unresolved Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
#Other important rules:#
4. You can go to the 'Bestsellers' of the '\\ue60a REPORTS' to filter the selling report within a period. (whether the mechanism is related to the existing rule)

### Check Difference:
Potential Rule 1 addresses the entire success process. Potential Rule 2 targetes .... They target different phenomena.

### Check Existing Rules:
* rule_0: ...(is not related to this trajectory). 
* rule_1: ...(is conflicted or need updating).

### Code:
```python
rule_manager.write_rule(
rule = "If the task need to identify the top best-selling band within a period, first go the link 'Bestsellers' in 'REPORTS'. Next, filter with the proper period and calculate the quantity for each band.",
type = "Success Process",
example = \'''# For example, to answer the top-1 best-selling band in Quarter 1 2022:
# [Step 1] Click link 'REPORTS'.
# [Step 2] Click link 'Bestsellers' to filter the report.
# [Step 3] Click the 'Period' box and select the option 'Month'.
# [Step 4] Type the begining and the ending of the time zone.
# [Step 5] Click the button 'Show Report'
# [Step 6] Manually figure out the top-1 best-selling band
\''',
validation_record = "This process adopts the method in 'rule_0' and is vaild by the success of epoch_0.")

rule_manager.write_rule(
rule = "You can go to the link 'Bestsellers' in the '\\ue60a REPORTS' to filter the selling report within a period.",
type = "Special Mechanism",
validation_record = "The agent can find a way to filter report after heading into 'Bestsellers' of '\\ue60a REPORTS' at epoch_0.")

rule_manager.stop_generating()
```
'''

worker_example = '''
Your task: What is the top-1 best-selling brand in Quarter 1 2022.
OBSERVATION: ...

### Understanding of the the task and observation: Because there is no explicit year filter visible in the observation, I need to find a way to filter the sales data with Quarter 1 2022. I will click [126] link '\\ue60a REPORTS' to find the filtered report.
### Rules to consider: ...
### Plan for the task: 1. Click the '\\ue60a REPORTS' link to find the way to filter report. 2. Type the time zone into the filter. 3. Figure out the top-1 best-selling band.
### Code:
```python
# Click the 'REPORTS' link
agent.click(126)
```

obs_1: Act: agent.click(126). Obs: click [126] where [126] is link '\\ue60a REPORTS'
OBSERVATION: ...
### Understanding of the observation: I can click [602] link 'Bestsellers' to find the report for best-selling products.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# Click the 'Bestsellers' link
agent.click(602)
```

obs_2: Act: agent.click(602). Obs: click [602] where [602] is link 'Bestsellers'
OBSERVATION: ...
### Understanding of the observation: Regarding the task, using 'Day' as the report 'Period' is not proper. First, switch the 'Period' of the report from 'Day' to 'Month'.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# Switch the 'Period' combobox
agent.click(1267)
```

obs_3: Act: agent.click(1267). Obs: click [1267] where [1267] is combobox 'Period' hasPopup: menu expanded: False
OBSERVATION: ...
### Understanding of the observation: Now I can select the period of the report. I need to select the option 'Month'.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# Select the option 'Month'
agent.click(1267, "Month")
```

obs_4: Act: agent.click(1267, "Month"). Obs: click [1267] where [1267] is combobox 'Period' focused: True hasPopup: menu expanded: True
OBSERVATION: ...
### Understanding of the observation: Then select the time zone.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# type the first day of 2022 into textbox 'From *'
agent.type(1270, "01/1/2022")

# type the last day of 2022 into textbox 'To *'
agent.type(1273, "3/31/2022")
```

obs_5: Act: agent.type(1270,"01/1/2022","True","True"). Obs: type [1270] [01/1/2022] where [1270] is textbox 'From *' required: True
obs_6: Act: agent.type(1273,"3/31/2022","True","True"). Obs: type [1273] [12/31/2022] where [1273] is textbox 'To *' required: True
OBSERVATION: ...
### Understanding of the observation: Click [1590] button 'Show Report' to show the filtered report
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# click the button 'Show Report'
agent.click(1590)
```

obs_7: Act: agent.click(1590). Obs: click [1590] where [1590] is button 'Show Report'
OBSERVATION: ...
### Understanding of the observation: I will manually count the Order Quantity for each band (the first word of the product).
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# Manually count and stop with the answer
agent.stop("Sprite")
```
'''.strip()