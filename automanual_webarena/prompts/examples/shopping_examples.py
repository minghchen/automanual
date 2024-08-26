init_rules = {
'rule_0': {"rule": "If the task need to list the reviewers whose review on a product contains some specific content, first click the Review link, then scroll and carefully check all comments one by one, and gather the required reviewers.", "type": "Success Process", "example": '''
# For example, to List out reviewers, if exist, who mention about ear cups being small:
# [Step 1] Click the link '12\xa0 Reviews' to view reviews.
# [Step 2] Scroll and carefully check all comments one by one, while paying attention to go to the next page if "Next Page" link exists.
# [Step 3] Gather the required reviewers.
''', "validation_record": "Provided by User."},
'rule_1': {"rule": "The content of a review may be cut off by the visible area and you need to scroll down to see the remaining content and its reviewer. Therefore, leave key information in your response and review key information from previous responses.", "type": "Special Mechanism", "example": "", "validation_record": "Provided by User."}
}

builder_example = '''
Previously discovered rules: \{...\}
Current epoch's trajectory: \{
'epoch_0_interact_0': "obs_0: Your task: List out reviewers, if exist, who mention about ear cups being small\nOBSERVATION: ...", 
'epoch_0_interact_1': "Agent's analysis: ...\nAgent's code: ```python
agent.click(265)
```
obs_1: Act: agent.click(265). Obs: click [265] where [265] is link '12\xa0 Reviews'\nOBSERVATION: ...",
...
'epoch_0_interact_6': "Agent's analysis: ...\nAgent's code: ```python
# Stop with the reviewers
agent.stop("Catso, Dibbins, Anglebert Dinkherhump, Michelle Davis")
```
obs_6: Act: agent.stop("Catso, Dibbins, Anglebert Dinkherhump, Michelle Davis"). Obs: Action has been performed. This epoch is done. Succeed: True"\}

### Outputs ###:
In this epoch, the agent completes the task of listing required reviewers on a product.
### Potential Rules:
1. #if success# *Success Process*: To list the reviewers whose review on a product contains some specific content, Steps 1 is to click the Review link, Steps 2 is to scroll to check all comments one by one, Steps 3 is to gather and answer the required reviewers. This success process hasn't been include in the scope of the existing 'Success Process' rule.
2. #if errors exist# *Corrected Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
3. #if failed# *Unresolved Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
#Other important rules:#
4. The content of a review may be cut off by the visible area. You need to scroll down to see the remaining content and its reviewer. (whether the mechanism is related to the existing rule)

### Check Difference:
Potential Rule 1 addresses the entire success process. Potential Rule 2 targetes .... They target different phenomena.

### Check Existing Rules:
* rule_0: ...(is not related to this trajectory). 
* rule_1: ...(is conflicted or need updating).

### Code:
```python
rule_manager.write_rule(
rule = "If the task need to list the reviewers whose review on a product contains some specific content, first click the Review link, then scroll and carefully check all comments one by one, and gather the required reviewers.",
type = "Success Process",
example = \'''
# For example, to List out reviewers, if exist, who mention about ear cups being small:
# [Step 1] Click the link '12\xa0 Reviews' to view reviews.
# [Step 2] Scroll and carefully check all comments one by one, while paying attention to go to the next page if "Next Page" link exists.
# [Step 3] Gather the required reviewers.
\''',
validation_record = "This process adopts the method in 'rule_0' and is vaild by the success of epoch_0.")

rule_manager.write_rule(
rule = "The content of a review may be cut off by the visible area. You need to scroll down to see the remaining content.",
type = "Special Mechanism",
validation_record = "A comment has only the title in view at epoch_0.")

rule_manager.stop_generating()
```
'''

worker_example = '''
Your task: List out reviewers, if exist, who mention about ear cups being small
OBSERVATION: ...

### Understanding of the task and observation: The task is to find specific reviewers, so I first need to find the Review section of this product. I am on a store page for a headphone and I see the link '12\xa0 Reviews'.
### Rules to consider: ...
### Plan for the task: 1. Navigate to the Review section. 2. Carefully check all reviews while recording the required reviewers. 3. Give the answer.
### Code:
```python
agent.click(265)
```

obs_1: Act: agent.click(265). Obs: click [265] where [265] is link '12\xa0 Reviews'
OBSERVATION: ...
### Understanding of the observation: I see the reviews and I need to carefully check them one by one. The first review is made by 'Jenna Kaufman', which is about the headphone is great and its battery, but doesn't mention about ear cups being small. The second review is made by 'Joseph Brzezinski', which methions 'a bit small for my tired ancient eyes', but is not about ear cups. The title of the thrid review methions 'Too small, did not hold charge', but I need to scroll down to view its reviewer.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
agent.scroll("down")
```

obs_2: Act: agent.scroll("down"). Obs: Action has been performed.
OBSERVATION: ...
### Understanding of the observation: Now I see the remaining content of the third review, which is made by 'Catso'. It methions ..., so **Catso** belongs to the demanded reviewers. The fourth review is made by 'Dibbins'...
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
agent.scroll("down")
```

obs_3: Act: agent.scroll("down"). Obs: Action has been performed.
OBSERVATION: ...
### Understanding of the observation: The sixth review ...
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
agent.scroll("down")
```

obs_4: Act: agent.scroll("down"). Obs: Action has been performed.
OBSERVATION: ...
### Understanding of the observation: The ninth review ... I see a pagination, which means I have finished reading the reviews on this page. I need to navigate to the next page to view the remaining reviews.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# click the link 'Page Next'
agent.click(2842)
```

obs_5: Act: agent.click(2842). Obs: click [2842] where [2842] is link '\ue608 Page Next'
OBSERVATION: ...
### Understanding of the observation: I see the reviews on the page 2. The eleventh review ... I have checked all reviews, and I need to summarize the reviewers required.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# Stop with the reviewers
agent.stop("Catso, Dibbins, Anglebert Dinkherhump, Michelle Davis")
```
'''.strip()