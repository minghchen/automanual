import re
from env_history import Agent, get_object_with_id, find_object, go_to_put_object
from OpenAI_Agent_API import get_ChatGPT_Agent, process_respond
from prompts.builder_case_prompt import *

MAX_REPLAN_STEP = 3
MAX_RULE_NUM = 12
def run(args, env, rule_manager, skill_bank):
    epoch_id = f"epoch_{env.epoch_id}"

    # Create the Planner and Builder Agent
    if args.simple_example:
        from prompts.autobuild_simple_examples import worker_example, builder_example
    else:
        from prompts.autobuild_examples import worker_example, builder_example
    Worker_agent = get_ChatGPT_Agent(args.model_name, "worker", "./prompts/worker_prompt.txt", args.assistant_api, example_list=[worker_example])
    Builder_agent = get_ChatGPT_Agent(args.model_name, "builder", "./prompts/builder_prompt.txt", args.assistant_api, example_list=[builder_example])

    # Get the trajectory of current epoch
    if epoch_id not in rule_manager.global_history:
        run_trail(args, env, rule_manager, skill_bank, Worker_agent)

    epoch_data = rule_manager.global_history[epoch_id]
    interact_history = epoch_data["interact_history"]
    is_success = epoch_data["is_success"]
    error_step = epoch_data["error_step"]
    
    # The Builder Agent manages rules based on the current trajectory
    if not rule_manager.global_history[epoch_id]['check_rule']:
        run_autobuild(interact_history, is_success, error_step, rule_manager, Builder_agent)
        rule_manager.global_history[epoch_id]['check_rule'] = True
        rule_manager.save()
    
    consumed_tokens = Worker_agent.consumed_tokens() + Builder_agent.consumed_tokens()

    # If the rule number exceed the maximum, the Consolidator Agent merges or delete rules
    consumed_tokens = run_merge(args, rule_manager, consumed_tokens)

    return is_success, error_step, consumed_tokens

def run_trail(args, env, rule_manager, skill_bank, Worker_agent):
    epoch_id = f"epoch_{env.epoch_id}"
    agent = Agent(env)

    # The worker starts trying to complete the current task
    local_vars = {'agent': agent, 'get_object_with_id': get_object_with_id, 'find_object': find_object, 'go_to_put_object': go_to_put_object, 're': re}
    rule_manager.define_functions_from_rules(local_vars)
    skill_string = skill_bank.get_relevant_skill(env.task_type, local_vars)
    Worker_agent.add_prompt(f"{rule_manager.rule_string()}\n{skill_string}")
    
    observation = env.init_info
    interact_history = {f"{epoch_id}_interact_0": f"obs_0: {observation}"}
    print(f"{rule_manager.rule_string()}\n{skill_string}\n{observation}")

    # The worker can replan for MAX_REPLAN_STEP times
    for cur_step in range(MAX_REPLAN_STEP):
        respond = Worker_agent.generate(observation)
        print(respond)
        # extract code block from the respond
        respond_thought, respond_code = process_respond(respond)
        # execute the solution code
        try:
            exec(respond_code, local_vars, local_vars)
        except Exception as e:
            if env.done and env.reward:
                error_msg = agent.report()
            else:
                error_msg = agent.report(error_msg=f"Execution error:\n{str(e)}\n")
        else:
            error_msg = agent.report()
            if not env.done:
                if cur_step==MAX_REPLAN_STEP-1:
                    error_msg += f"You have responded too many times, exceeding the number of response allowed to complete the task: {MAX_REPLAN_STEP} times. The task is not completed. Succeed: False"
                else:
                    error_msg += "\nNotice: Your code has been executed and the task is not completed. Please write code to complete the task from the current situation."
        observation = error_msg
        print(observation)
        # recode the interaction into history
        interact_id = f"{epoch_id}_interact_{cur_step+1}"
        interact_history[interact_id] = f"Agent's analysis: {respond_thought}\nAgent's code:```python\n{respond_code}\n```\nFeedback: {observation}"
        if env.done:
            break
    # add the experience to skill bank based on the result 
    is_success = env.reward
    direct_success = (is_success and cur_step == 0)
    indirect_success = (is_success and cur_step >= 1)
    # summarize the success code and add it to skill bank
    if is_success:
        if indirect_success:
            respond = Worker_agent.generate(observation+worker_conclusion_prompt)
            print(respond)
            respond_thought, respond_code = process_respond(respond)
            interact_history[f"{epoch_id}_conclusion"] = f"User: summarize and reorganize the success code.\nAgent: {respond}"
        skill_bank.add_skill(env.task_type, env.task, env.init_obs, respond_code, direct_success)
    else:
        # generate the reflection for failure
        respond = Worker_agent.generate(observation+worker_reflection_prompt)
        print(respond)
        _, _ = process_respond(respond, check_code=False)
        interact_history[f"{epoch_id}_conclusion"] = f"User: summarize the mistake led to failure.\nAgent: {respond}"
        skill_bank.add_failure(env.task_type, env.task, env.init_obs, respond)
    skill_bank.save()
    rule_manager.add_epoch_history(env.epoch_id, env.task_type, interact_history, env.env_history, env.reward, cur_step)
    rule_manager.save()    

def run_autobuild(interact_history, is_success, error_step, rule_manager, Builder_agent):
    print("\nBegin extracting rules from the current epoch.\n")
    Builder_agent.add_prompt(f"Print rule_manager.all_rules:\n{str(rule_manager.all_rules)}\nCurrent epoch's trajectory:\n")
    for interact_id, interaction in interact_history.items():
        Builder_agent.add_prompt(f"'{interact_id}': {interaction}\n")
    respond = Builder_agent.generate()
    print(respond)
    respond_thought, respond_code = process_respond(respond)
    # execute the solution code
    exec(respond_code)
    tool_messages = rule_manager.report()
    print(tool_messages)

def run_merge(args, rule_manager, consumed_tokens):
    while len(rule_manager.all_rules) > MAX_RULE_NUM:
        print(f"\nToo many rules exist: {len(rule_manager.all_rules)} > {MAX_RULE_NUM}. Begin merging.\n")
        Builder_merge_agent = get_ChatGPT_Agent(args.model_name, "builder_merge", "./prompts/builder_merge_prompt.txt", args.assistant_api, example_list=None)
        message = builder_merge_get_prompt.format(str(rule_manager.all_rules), MAX_RULE_NUM)
        respond = Builder_merge_agent.generate(message)
        print(respond)
        respond_thought, respond_code = process_respond(respond)
        exec(respond_code)
        message = rule_manager.report()
        rule_manager.arrange_rules()
        consumed_tokens += Builder_merge_agent.consumed_tokens()
    
    rule_manager.save()
    return consumed_tokens