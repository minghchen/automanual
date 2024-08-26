init_rules = {
'rule_0': {"rule": "If the idx of the target search result exceeds 3 (the number of results per page), use 'turn_to_next_page' method as shown in the example.", "type": "Useful Helper Method", "example": '''# Turn to the next page.
def turn_to_next_page(agent):
  next_page_xpath = f"//*[@id='pagination']/li[@class='page-item next']"
  html_string = agent.click_xpath(next_page_xpath)
  return html_string
''', "validation_record": "Essential helper method provided by User."},
'rule_1': {"rule": "If the task need to use search engine, first click <input> textbox, type the target string, and then click \"Search\" button. Next, use 'turn_to_next_page' to turn the page if the target idx exceed 3 and click the target result.", "type": "Success Process", "example": '''# For example, to search Jerald and click the 4th result:
# [Step 1] Find <input> textbox and type "Jerald".
# [Step 2] Click the search button.
# [Step 3] Use 'turn_to_next_page' method to turn the page and click the target result.
''', "validation_record": "Provided by User."}
}

builder_example = '''
Previously discovered rules: \{...\}
Current epoch's trajectory: \{
'epoch_0_interact_0': "obs_0: Your task is to Use the textbox to enter "Jerald" and press "Search", then find and click the 4th search result.\n...(HTML)...", 
'epoch_0_interact_1': "Agent's analysis: ...\nAgent's code: ```python
# [Step 1] Find <input> textbox and type "Jerald".
...(code)...

# [Step 2] Click the search button
search_button_xpath = "//*[@id='search']"
html_string = agent.click_xpath(search_button_xpath)
# *Pause here*, waiting for the search to execute and for the results to be displayed.

# Write a helper method that can turn to the next page.
def turn_to_next_page(agent):
  ...(code)...

# [Step 3] Use 'turn_to_next_page' method to turn to the next page for the 4th search result and click the result
...(code)...
```
Feedback: 
...(some feedbacks)...
obs_5: Act: agent.click_xpath("//*[@id='page-content']//a[@data-result='3']"). Obs: Action done. The epoch is Done. Succeed: True."\}

### Outputs ###:
In this epoch, the agent complete the task of using search engine.

### Potential Rules:
1. #if success# *Success Process*: To use search engine, Steps 1 is to click <input> textbox and type the target string. Steps 2 is to click "Search" button and make assertion of the result. Step 3 is to use 'turn_to_next_page' method if the target idx exceed 3 and click the target result. This success process hasn't been include in the scope of the existing 'Success Process' rule.
2. #if success and helper method exists# *Helper method*: The 'turn_to_next_page' method is successfully used to turn to the next page. This helper method doesn't overlap with the existing 'Useful Helper Method' rule.
3. #if errors exist# *Corrected Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
4. #if failed# *Unresolved Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
#Other important rules:#
5. The search results, 'search-title', 'search-url' and 'search-desc', can be observed after clicking "Search" button (whether the mechanism is related to the existing rule)

### Check Difference:
Potential Rule 1 addresses the entire success process. Potential Rule 2 targetes the 'turn_to_next_page' method..... They target different phenomena.

### Check Existing Rules:
* rule_0: ...(is not related to this trajectory). 
* rule_1: ...(is conflicted or need updating).

### Code:
```python
rule_manager.write_rule(
rule = "If the idx of the target search result exceeds 3 (the number of results per page), use 'turn_to_next_page' method as shown in the example.",
type = "Useful Helper Method",
example = \'''# Turn to the next page.
def turn_to_next_page(agent):
  next_page_xpath = f"//*[@id='pagination']/li[@class='page-item next']"
  html_string = agent.click_xpath(next_page_xpath)
  return html_string
\''',
validation_record = "The 'turn_to_next_page' method shows it can successfully turn to the next page in epoch_0.")

rule_manager.write_rule(
rule = "If the task need to use search engine, first click <input> textbox, type the target string, and then click \"Search\" button. Next, use 'turn_to_next_page' to turn the page if the target idx exceed 3 and click the target result.",
type = "Success Process",
example = \'''# For example, to search Jerald and click the 4th result:
# [Step 1] Find <input> textbox and type "Jerald".
# [Step 2] Click the search button.
# [Step 3] Use 'turn_to_next_page' method to turn the page and click the target result.
\''',
validation_record = "This process adopts the method in 'rule_0' and is vaild by the success of epoch_0.")

rule_manager.write_rule(
rule = "The search results, 'search-title', 'search-url' and 'search-desc', after clicking \"Search\" button...",
type = "Special Mechanism",
validation_record = "The agent can observe the search results after click \"Search\" button at epoch_0.")

rule_manager.stop_generating()
```
'''

worker_example = '''
Currently found rules:
rule_0 (type=Useful Helper Method): If the idx of the target search result exceeds 3 (the number of results per page), use 'turn_to_next_page' method as shown in the example. For example, 
def turn_to_next_page(agent):
  next_page_xpath = f"//*[@id='pagination']/li[@class='page-item next']"
  html_string = agent.click_xpath(next_page_xpath)
  return html_string
rule_1: ...

Your task is to Use the textbox to enter "Jerald" and press "Search", then find and click the 4th search result.
...(HTML)...

### Outputs ###

### Understanding of the observation: ...
### Rules to consider: ...
### Plan for the task: I need to click <input> textbox and type "Jerald". Then I need to click "Search" button and get the searching result. Finally, navigate to and click on the 4th search result.
### Code:
```python
# [Step 1] Find <input> textbox and type "Jerald".
textbox_xpath = "//*[@id='search-text']"
agent.click_xpath(textbox_xpath)
agent.type("Jerald")

# [Step 2] Click the search button
search_button_xpath = "//*[@id='search']"
html_string = agent.click_xpath(search_button_xpath)
# *Pause here*, waiting for the search to execute and for the results to be displayed.
```

### Feedbacks ###
...(some feedbacks)...
...(resulting HTML)...

### Outputs ###

### Understanding of the observation: ... Because one page only display 3 search results, I need to turn to the next page for the 4th search result.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# 'turn_to_next_page' method in rule_0 can be used to turn to the next page. I can directly call it without modification.

# [Step 3] Use 'turn_to_next_page' method to turn to the next page for the 4th search result and click the result
html_string = turn_to_next_page(agent)
result_xpath = f"//*[@id='page-content']//a[@data-result='3']" # data-result start from 0
agent.click_xpath(result_xpath)
```
'''.strip()

formulater_example = '''
Print rule_manager.all_rules: \{'rule_0': ..., 'rule_1': ..., ...\}

### General Understandings: ...

### Category of Rules: ...

Here is the resulting manual:
```markdown
# Manual Name

## Overview

Briefly introduce the topics covered and the main objectives of the rules.

## Category 1 Name

### Introduction

A brief description of the category, what the rules have in common, and highlighting key contents.

#### Included Ruls

- **rule_3**: A short rule description
- **rule_10**: A short rule description

## Category 2 Name

### Introduction

A brief description of the category, what the rules have in common, and highlighting key contents.

#### Included Ruls

- **rule_1**: A short rule description
- **rule_4**: A short rule description
...
```
'''
