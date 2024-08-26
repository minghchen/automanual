init_rules = {
'rule_0': {"rule": "If the task need to identify the user who made the latest post on a forum and count required comments from the user, first locate the forum, find the latest post. Next, view the profile of the user who submitted it and count required comments.", "type": "Success Process", "example": '''# For example, to count the comments that have received more downvotes than upvotes for the user who made the latest post on the Showerthoughts forum:
# [Step 1] Click link 'Forums'.
# [Step 2] Click link 'Alphabetical' to see all forums.
# [Step 3] Click the Showerthoughts forum
# [Step 4] Sort the posts by newest
# [Step 5] Click the link to the user who made the latest post
# [Step 6] Count the comments that have received more downvotes than upvotes for the user
''', "validation_record": "Provided by User."},
'rule_1': {"rule": "If you want to find a target forum, it may not appear on the 'Forums' homepage. But you can use the link 'Alphabetical' to see all forums alphabetically.", "type": "Special Mechanism", "example": '''
# After clicking the 'Forums' link
agent.click(749) # where [749] is link 'Alphabetical'
''', "validation_record": "Provided by User."}
}

builder_example = '''
Previously discovered rules: \{...\}
Current epoch's trajectory: \{
'epoch_0_interact_0': "obs_0: Your task: Tell me the count of comments that have received more downvotes than upvotes for the user who made the latest post on the Showerthoughts forum.\nOBSERVATION: ...",
'epoch_0_interact_1': "Agent's analysis: ...\nAgent's code: ```python
# Click the 'Forums' link
agent.click(66)
```
obs_1: Act: agent.click(66). Obs: click [66] where [66] is link 'Forums'\nOBSERVATION: ...",
'epoch_0_interact_2': "Agent's analysis: ...\nAgent's code: ```python
agent.click(749)
```
obs_2: Act: agent.click(749). Obs: click [749] where [749] is link 'Alphabetical'\nOBSERVATION: ...",
...
'epoch_0_interact_7': 
"Agent's analysis: ...\nAgent's code: ```python
# Stop with the count
agent.stop("0")
```
obs_7: Act: agent.stop("0"). Obs: Action has been performed. This epoch is done. Succeed: True"\}

### Outputs ###:
In this epoch, the agent completes the task of counting required comments in a specific forum.
### Potential Rules:
1. #if success# *Success Process*: To identify the user who made the latest post on a forum and count required comments from the user, Steps 1 is to click the 'Forums' link and locate the forum, Steps 2 is to sort posts by the newest there, Steps 3 is to click the user who made the latest post and view his profile, Steps 4 is to count his comments as required. This success process hasn't been include in the scope of the existing 'Success Process' rule.
2. #if errors exist# *Corrected Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
3. #if failed# *Unresolved Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
#Other important rules:#
4. The target forum may not appear on the 'Forums' homepage. You can use the link 'Alphabetical' to search for forums alphabetically. (whether the mechanism is related to the existing rule)

### Check Difference:
Potential Rule 1 addresses the entire success process. Potential Rule 2 targetes .... They target different phenomena.

### Check Existing Rules:
* rule_0: ...(is not related to this trajectory). 
* rule_1: ...(is conflicted or need updating).

### Code:
```python
rule_manager.write_rule(
rule = "If the task need to identify the user who made the latest post on a forum and count required comments from the user, first locate the forum, find the latest post. Next, view the profile of the user who submitted it and count required comments.",
type = "Success Process",
example = \'''# For example, to count the comments that have received more downvotes than upvotes for the user who made the latest post on the Showerthoughts forum:
# [Step 1] Click link 'Forums'.
# [Step 2] Click link 'Alphabetical' to see all forums.
# [Step 3] Click the Showerthoughts forum
# [Step 4] Sort the posts by newest
# [Step 5] Click the link to the user who made the latest post
# [Step 6] Count the comments that have received more downvotes than upvotes for the user
\''',
validation_record = "This process adopts the method in 'rule_0' and is vaild by the success of epoch_0.")

rule_manager.write_rule(
rule = "If you want to find a target forum, it may not appear on the 'Forums' homepage. But you can use the link 'Alphabetical' to see all forums alphabetically.",
type = "Special Mechanism",
validation_record = "The agent can observe all formus after clicking the link 'Alphabetical' at epoch_0.")

rule_manager.stop_generating()
```
'''

worker_example = '''
Your task: Tell me the count of comments that have received more downvotes than upvotes for the user who made the latest post on the Showerthoughts forum.
OBSERVATION: ...

### Understanding of the task and observation: Because the task is related to the latest post on the Showerthoughts forum, I first need to click [66] link 'Forums' to find the Showerthoughts forum.
### Rules to consider: ...
### Plan for the task: 1. Click the 'Forums' link to locate the Showerthoughts forum. 2. Find the latest post there. 3. Identify the user who made the latest post to view his profile. 4. Count his comments as required.
### Code:
```python
# Click the 'Forums' link
agent.click(66)
```

obs_1: Act: agent.click(66). Obs: click [66] where [66] is link 'Forums'
OBSERVATION: ...
### Understanding of the observation: The Showerthoughts forum is not observed. But I can click [749] link 'Alphabetical' to see all forums.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
agent.click(749)
```

obs_2: Act: agent.click(749). Obs: click [749] where [749] is link 'Alphabetical'
OBSERVATION: ...
### Understanding of the observation: Now I see the Showerthoughts forum.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# click the link 'Showerthoughts'
agent.click(1523)
```

obs_3: Act: agent.click(1523). Obs: click [1523] where [1523] is link 'Showerthoughts'
OBSERVATION: ...
### Understanding of the observation: The current posts on the Showerthoughts forum is sort by 'Hot'. But the task needs to find the user who made the latest post, so I need to sort the posts by the time.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# click the button 'Sort by: Hot'
agent.click(1767)
```

obs_4: Act: agent.click(1767). Obs: click [1767] where [1767] is button 'Sort by: Hot'
OBSERVATION: ...
### Understanding of the observation: Sort the posts by the newest.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# click the link 'New'
agent.click(3517)
```

obs_5: Act: agent.click(3517). Obs: click [3517] where [3517] is link 'New'
OBSERVATION: ...
### Understanding of the observation: Click the user who submitted the newest post.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# click the link 'nirinaron'
agent.click(3558)
```

obs_6: Act: agent.click(3558). Obs: click [3558] where [3558] is link 'nirinaron'
OBSERVATION: ...
### Understanding of the observation: Because this user leaves no comment, the count of comments that have received more downvotes than upvotes for this user is 0.
### Rules to consider: ...
### Plan for the task: ...
### Code:
```python
# Stop with the count
agent.stop("0")
```
'''.strip()