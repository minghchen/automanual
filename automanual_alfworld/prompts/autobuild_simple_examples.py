init_rules = {
'rule_0': {"rule": "At the initial observation of the environment, the agent can only observe receptacles, such as cabinet_1, countertop_1. The agent needs to go to the receptacle to view objects in or on it, even for open receptacles.", "type": "Special Mechanism", "example": "", "validation_record": "Provided by User."},
'rule_1': {"rule": "If there are multiple receptacles to be search, the agent can write and use 'find_object' method as shown in the example. The closed receptacle will be opened before checking.", "type": "Useful Helper Method", "example": '''# Define helper method to find object that is needed
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
''', "validation_record": "Essential helper method provided by User."}
}

builder_example = '''
Previously discovered rules: \{...\}
Current epoch's trajectory: \{
'epoch_0_interact_0': "obs_0: ...\nYour task is to: find some spraybottle.", 
'epoch_0_interact_1': "Agent's analysis: ...\nAgent's code: ```python
# Define helper method to find object that is needed
def find_object(agent, recep_to_check, object_name):
    ...(code)...

# [Step 1] get a sorted list of receptacles where the spraybottle is likely to appear.
recep_to_check = ...

# [Step 2] go to each receptacle in the list until seeing a spraybottle
object_ids, receptacle_with_spraybottle = find_object(agent, recep_to_check, 'spraybottle')
assert object_ids is not None, f'Error in [Step 2]: There is no spraybottle in/on {recep_to_check}.'
```
Feedback: 
...(some feedbacks)...
obs_3: Act: agent.open('cabinet_2'). Obs: You open cabinet_2. In cabinet_2, you see candle_1, and spraybottle_2. You are at cabinet_2 and holding nothing. This epoch is done. Succeed: True"
\}

### Outputs ###
In this epoch, the agent successfully complete the task of 'find some spraybottle'.

### Potential Rules:
1. #if success# *Success Process*: To find some object, Steps 1 is to get a ordered list of receptacles where the object is likely to appear. Steps 2 is to use 'find_object' method and make assertion of the result. This success process hasn't been include in the scope of the existing 'Success Process' rule.
2. #if success and helper method exists# *Helper method*: The 'find_object' method is successfully used to search multiple receptacles. In this method, "for" is used to automatically search the receptacles. Additionally, the initial state of a receptacle can be opened or closed, so the method check the receptacle's state first then check the objects in it. This helper method doesn't overlap with the existing 'Useful Helper Method' rule.
3. #if errors exist# *Corrected Error*:...(summarize how the error occur)...(whether the error is closely related to the existing rule)
4. #if failed# *Unresolved Error*:...(summarize how the error occur)...(whether the error is closely related to the existing rule)
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
rule = "If the task need to find some object, first generate a list of receptacles that the object is likely to appear, then use 'find_object' method to search the receptacles.",
type = "Success Process",
example = \'''# For example, to find a spraybottle:
# [Step 1] get a list of receptacles where the spraybottle is likely to appear.
recep_to_check = ...
# [Step 2] use 'find_object' method to search each receptacle in the list until seeing a spraybottle
object_ids, receptacle_with_spraybottle = find_object(agent, recep_to_check, 'spraybottle')
assert object_ids is not None, f'There is no spraybottle in/on {recep_to_check}.'
\''',
validation_record = "This process adopts the method in 'rule_1' and is vaild by the success of epoch_0.")

rule_manager.stop_generating()
```
'''

worker_example = '''
You are in the middle of a room. Looking quickly around you, you see cabinet_4, cabinet_3, cabinet_2, cabinet_1, countertop_1, garbagecan_1, sinkbasin_2, sinkbasin_1, toilet_2, toilet_1.
Your task is to: find some spraybottle.

### Understanding of the observation: ...
### Rules to consider: ...
### Plan for the task: Get a list of receptacles where the spraybottle is likely to appear, then go to search each receptacle until seeing a spraybottle.
### Code:
```python
# Define helper method to find object that is needed
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

# [Step 1] get a sorted list of receptacles where the spraybottle is likely to appear.
recep_to_check = ['cabinet_1', 'cabinet_2', 'cabinet_3', 'cabinet_4', 'countertop_1', 'toilet_2', 'toilet_1', 'sinkbasin_1', 'sinkbasin_2', 'garbagecan_1']

# [Step 2] go to each receptacle in the list until seeing a spraybottle
object_ids, receptacle_with_spraybottle = find_object(agent, recep_to_check, 'spraybottle')
assert object_ids is not None, f'Error in [Step 2]: There is no spraybottle in/on {recep_to_check}.'
```

### Feedbacks ###
obs_1: Act: agent.go_to('cabinet_1'). Obs: On cabinet_1, you see cloth_1, soapbar_1, soapbottle_1. You are at cabinet_1 and holding nothing.
obs_2: Act: agent.go_to('cabinet_2'). Obs: cabinet_2 is closed. You are at cabinet_2 and holding nothing.
obs_3: Act: agent.open('cabinet_2'). Obs: You open cabinet_2. In cabinet_2, you see candle_1, and spraybottle_2. You are at cabinet_2 and holding nothing. This epoch is done. Succeed: True
'''.strip()