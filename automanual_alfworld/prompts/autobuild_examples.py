init_rules = {
'rule_0': {"rule": "At the initial observation of the environment, the agent can only observe receptacles, such as cabinet_1, countertop_1. The agent needs to go to the receptacle to view objects in or on it, even for open receptacles.", "type": "Special Mechanism", "example": "", "validation_record": "Provided by User."},
'rule_1': {"rule": "If there are multiple receptacles to be searched, the agent can write and use the 'find_object' method as shown in the example.", "type": "Useful Helper Method", "example": '''# Define helper method to find the object that is needed
def find_object(agent, recep_to_check, object_name):
    for receptacle in recep_to_check:
        observation = agent.go_to(receptacle)
        # Check if we need to open the receptacle. If we do, open it.
        if 'closed' in observation:
            observation = agent.open(receptacle)
        # Check if the object is in/on the receptacle.
        if object_name in observation:
            object_ids = get_object_with_id(observation, object_name)
            return object_ids, receptacle
    return None, None
''', "validation_record": "Essential helper method provided by User."},
'rule_2': {"rule": "If the task is to put some object on some receptacle, first use 'find_object' method in rule_1 to search receptacles, take the object, then go to the target receptacle and put the object.", "type": "Success Process", "example": '''# For example, to put some spraybottle on toilet:
# [Step 1] Use 'find_object' method in rule_1 to search receptacles
recep_to_check = ...
object_ids, receptacle_with_spraybottle = find_object(agent, recep_to_check, 'spraybottle')
# [Step 2] Take the spraybottle
# [Step 3] Go to a toilet and put the spraybottle on it
# If the toilet is closed, open it first.
''', "validation_record": "Provided by User."}
}

builder_example = '''
Print rule_manager.all_rules: \{...\}
Current epoch's trajectory: \{
'epoch_0_interact_0': "obs_0: ...\nYour task is to: put some spraybottle on toilet.", 
'epoch_0_interact_1': "Agent's analysis: ...\nAgent's code: ```python
# Define a helper method to search receptacles for the target object
def find_object(agent, recep_to_check, object_name):
    ...(code)...

# [Step 1] Get a sorted list of receptacles and surfaces to check for a spraybottle. And use 'find_object' method to search
recep_to_check = ...
object_ids, receptacle_with_spraybottle = find_object(agent, recep_to_check, 'spraybottle')
...(assertion code)...

# [Step 2] Take the spraybottle
...(code)...

# [Step 3] Go to a toilet and put the spraybottle on it
...(code)...
```
Feedback: 
...(some feedbacks)...
obs_6: Act: agent.put_in_or_on('spraybottle_2', 'toilet_1'). Obs: You put spraybottle_2 in/on toilet_1. You are at toilet_1 and holding nothing. This epoch is done. Succeed: True"
\}

### Outputs ###
In this epoch, the agent successfully complete the task of 'put some spraybottle on toilet'.

### Potential Rules:
1. #if success# *Success Process*: To put some object on some receptacle, Steps 1 is to use 'find_object' method to search receptacles. Steps 2 is to take the object. Steps 3 is to go to the target receptacle and put the object. This success process hasn't been include in the scope of the existing 'Success Process' rule.
2. #if success and helper method exists# *Helper method*: The 'find_object' method is successfully used to search multiple receptacles. In this method, "for" is used to automatically search the receptacles. Additionally, the initial state of a receptacle can be opened or closed, so the method check the receptacle's state first then check the objects in it. This helper method doesn't overlap with the existing 'Useful Helper Method' rule.
3. #if errors exist# *Corrected Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
4. #if failed# *Unresolved Error*:...(summarize how the error occur)...(whether the error is related to the existing rule)
#Other important rules:#
5. At the initial observation of the environment, the agent can only observe receptacles, such as cabinet_1, countertop_1. The agent needs to go to the receptacle to view objects in or on it, even for open receptacles. This mechanism is unusual and may be useful for planning purposes. (whether the mechanism is related to the existing rule)

### Check Difference:
Potential rule 1 addresses the entire success process. Potential rule 2 targetes the 'find_object' method..... They target different phenomena.

### Check Existing Rules: 
* rule_0: ...(is not related to this trajectory). 
* rule_1: ...(is conflicted or need updating).

### Code:
```python
rule_manager.write_rule(
rule = "At the initial observation...",
type = "Special Mechanism",
validation_record = "At epoch_0, the agent only observe receptacles at the initial state, and it see objects after go_to the receptacles.")

rule_manager.write_rule(
rule = "If there are multiple receptacles to be search, use 'find_object' method as shown in the example.",
type = "Useful Helper Method",
example = \'''# Define helper method to find object that is needed
def find_object(agent, recep_to_check, object_name):
    for receptacle in recep_to_check:
        observation = agent.go_to(receptacle)
        # Check if we need to open the receptacle. If we do, open it.
        if 'closed' in observation:
            observation = agent.open(receptacle)
        # Check if the object is in/on the receptacle.
        if object_name in observation:
            object_ids = get_object_with_id(observation, object_name)
            return object_ids, receptacle
    return None, None
\''',
validation_record = "The 'find_object' method shows it can successfully search receptacles in epoch_0.")

rule_manager.write_rule(
rule = "If the task is to put some object on some receptacle, first use 'find_object' method in rule_1 to search receptacles, take the object, then go to the target receptacle and put the object.",
type = "Success Process",
example = \'''# For example, to put some spraybottle on toilet:
# [Step 1] Use 'find_object' method in rule_1 to search receptacles
recep_to_check = ...
object_ids, receptacle_with_spraybottle = find_object(agent, recep_to_check, 'spraybottle')
# [Step 2] Take the spraybottle
# [Step 3] Go to a toilet and put the spraybottle on it
# If the toilet is closed, open it first.
\''',
validation_record = "This process adopts the method in rule_1 and is vaild by the success of epoch_0.")

rule_manager.stop_generating()
```
'''

worker_example = '''
You are in the middle of a room. Looking quickly around you, you see cabinet_4, cabinet_3, cabinet_2, cabinet_1, countertop_1, garbagecan_1, sinkbasin_2, sinkbasin_1, toilet_2, toilet_1.
Your task is to: find some spraybottle.

### Understanding of the observation: ...
### Rules to consider: ...
### Plan for the task: I need to go to search each receptacle or surface until seeing a spraybottle. Then, I will take the spraybottle and put it on toilet_1.
### Code:
```python
# Define a helper method to search receptacles for the target object
def find_object(agent, recep_to_check, object_name):
    for receptacle in recep_to_check:
        observation = agent.go_to(receptacle)
        # Check if we need to open the receptacle. If we do, open it.
        if 'closed' in observation:
            observation = agent.open(receptacle)
        # Check if the object is in/on the receptacle.
        if object_name in observation:
            object_ids = get_object_with_id(observation, object_name)
            return object_ids, receptacle
    return None, None

# [Step 1] Get a sorted list of receptacles and surfaces to check for a spraybottle. And use 'find_object' method to search
recep_to_check = ['cabinet_1', 'cabinet_2', 'cabinet_3', 'cabinet_4', 'countertop_1', 'toilet_1', 'toilet_2', 'sinkbasin_1', 'sinkbasin_2', 'garbagecan_1']
object_ids, receptacle_with_spraybottle = find_object(agent, recep_to_check, 'spraybottle')
assert object_ids is not None, f'Error in [Step 1]: There is no spraybottle in/on {recep_to_check}.'

# [Step 2] Take the spraybottle
found_spraybottle = object_ids[0]
observation = agent.take_from(found_spraybottle, receptacle_with_spraybottle)
assert agent.holding == found_spraybottle, f'Error in [Step 2]: I cannot take {found_spraybottle} from {receptacle}.'

# [Step 3] Go to a toilet and put the spraybottle on it
observation = agent.go_to('toilet_1')
# check if toilet_1 is closed. If so, open it.
if 'closed' in observation:
    observation = agent.open('toilet_1')
observation = agent.put_in_or_on(found_spraybottle, 'toilet_1')
```

### Feedbacks ###
obs_1: Act: agent.go_to('cabinet_1'). Obs: On cabinet_1, you see cloth_1, soapbar_1, soapbottle_1. You are at cabinet_1 and holding nothing.
obs_2: Act: agent.go_to('cabinet_2'). Obs: cabinet_2 is closed. You are at cabinet_2 and holding nothing.
obs_3: Act: agent.open('cabinet_2'). Obs: You open cabinet_2. In cabinet_2, you see candle_1, and spraybottle_2. You are at cabinet_2 and holding nothing.
obs_4: Act: agent.take_from('spraybottle_2', 'cabinet_2'). Obs: You take spraybottle_2 from cabinet_2. You are at cabinet_2 and holding spraybottle_2.
obs_5: Act: agent.go_to('toilet_1'). Obs: On toilet_1, you see glassbottle_1. You are at toilet_1 and holding spraybottle_2.
obs_6: Act: agent.put_in_or_on('spraybottle_2', 'toilet_1'). Obs: You put spraybottle_2 in/on toilet_1. You are at toilet_1 and holding nothing. This epoch is done. Succeed: True
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