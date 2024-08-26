
find_example = '''
You are in the middle of a room. Looking quickly around you, you see cabinet_4, cabinet_3, cabinet_2, cabinet_1, countertop_1, garbagecan_1, sinkbasin_2, sinkbasin_1, toilet_2, toilet_1.
Your task is to: find some spraybottle.

### Outputs ###

General Plan: I need to get a list of receptacles where the spraybottle is likely to appear, and then go to search each receptacle until seeing a spraybottle.

Code:
\'''python
# [Step 1] get a list of receptacles where the spraybottle is likely to appear.
recep_to_check = ['cabinet_1', 'cabinet_2', 'cabinet_3', 'cabinet_4', 'countertop_1', 'toilet_1', 'sinkbasin_1', 'sinkbasin_2', 'garbagecan_1']

# [Step 2] go to each receptacle in the list until seeing a spraybottle
for receptacle in recep_to_check:
    observation = agent.go_to(receptacle)
        # check if the receptacle is closed. If so, open it.
        if 'closed' in observation:
            observation = agent.open(receptacle)
        # check if a spraybottle is in/on the receptacle.
        if 'spraybottle' in observation:
            break
assert 'spraybottle' in observation, f'Error in [Step 2]: There is no spraybottle in/on {recep_to_check}.'
\'''
'''.strip()

put_example = '''
You are in the middle of a room. Looking quickly around you, you see cabinet_4, cabinet_3, cabinet_2, cabinet_1, countertop_1, garbagecan_1, handtowelholder_2, handtowelholder_1, sinkbasin_2, sinkbasin_1, toilet_1, toiletpaperhanger_1, and towelholder_1.
Your task is to: put some spraybottle on toilet.

### Outputs ###

General Plan: I need to get a list of receptacles where the spraybottle is likely to appear, and then go to search each receptacle until seeing a spraybottle. Then take the spraybottle. Finally go to the toilet and put the spraybottle.

Code:
\'''python
# [Step 1] get a list of receptacles where the spraybottle is likely to appear.
recep_to_check = ['cabinet_1', 'cabinet_2', 'cabinet_3', 'cabinet_4', 'countertop_1', 'toilet_1', 'sinkbasin_1', 'sinkbasin_2', 'garbagecan_1']

# [Step 2] go to each receptacle in the list until seeing a spraybottle
for receptacle in recep_to_check:
    observation = agent.go_to(receptacle)
        # check if the receptacle is closed. If so, open it.
        if 'closed' in observation:
            observation = agent.open(receptacle)
        # check if a spraybottle is in/on the receptacle.
        if 'spraybottle' in observation:
            break
assert 'spraybottle' in observation, f'Error in [Step 2]: There is no spraybottle in/on {recep_to_check}.'

# [Step 3] take the spraybottle
found_spraybottle = get_object_with_id(observation, spraybottle)[0]
observation = agent.take_from(found_spraybottle, receptacle)
assert agent.holding == found_spraybottle, f'Error in [Step 3]: I cannot take {found_spraybottle} from {receptacle}.'

# [Step 4] go to a toilet and put the spraybottle on it
# There are multiple toilets, and I only need to go to one of them.
observation = agent.go_to('toilet_1')
# check if toilet_1 is closed. If so, open it.
if 'closed' in observation:
    observation = agent.open('toilet_1')
observation = agent.put_in_or_on(found_spraybottle, 'toilet_1')
assert f'You put {found_spraybottle} in/on toilet_1.' in observation, f'Error in [Step 4]: I cannot put {found_spraybottle} on toilet_1.'
\'''
'''.strip()