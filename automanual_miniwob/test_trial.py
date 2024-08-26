import re
from bs4 import BeautifulSoup
from OpenAI_Agent_API import get_ChatGPT_Agent, process_respond
from env_history import Agent, click_and_type, turn_to_next_page

MAX_REPLAN_STEP = 6
def run(args, env, rule_manager, skill_bank):
    agent = Agent(env)

    # Create the Planner Agent and load the demonstration
    if "autobuild" in args.agent_type:
        if args.simple_example:
            from prompts.autobuild_simple_examples import worker_example
        else:
            from prompts.autobuild_examples import worker_example
        Worker_agent = get_ChatGPT_Agent(args.model_name, "worker", "./prompts/worker_prompt.txt", args.assistant_api, example_list=[worker_example])
    else:
        from prompts.base_examples import enter_example, search_example
        worker_example = enter_example if args.simple_example else search_example
        Worker_agent = get_ChatGPT_Agent(args.model_name, "worker", "./prompts/base_prompt.txt", args.assistant_api, example_list=[worker_example])

    # Get the prompt of rules and relevant skills
    local_vars = {'agent': agent, 'click_and_type': click_and_type, 'turn_to_next_page': turn_to_next_page, 're': re, 'BeautifulSoup': BeautifulSoup}
    rule_manager.define_functions_from_rules(local_vars)
    skill_string = skill_bank.get_relevant_skill(env.task_type, local_vars)
    observation = env.init_info
    observation = f"{rule_manager.rule_string()}\n{skill_string}\n{observation}"
    error_step = 0
    print(observation)
    # The Planner Agent starts trying to complete the current task
    for cur_step in range(MAX_REPLAN_STEP):
        respond = Worker_agent.generate(observation)
        print(respond)
        if args.model_name == "human":
            respond_code = respond
        else:
            respond_thought, respond_code = process_respond(respond)
        # execute the solution code
        try:
            exec(respond_code, local_vars, local_vars)
        except Exception as e:
            if env.done and env.reward:
                error_msg = agent.report_action_history()
            else:
                error_msg = agent.report_action_history(error_msg=f"Execution error:\n{str(e)}\n")
                error_step += 1
        else:
            error_msg = agent.report_action_history()
            if not env.done:
                if cur_step==MAX_REPLAN_STEP-1:
                    error_msg += f"You have responded too many times, exceeding the number of response allowed to complete the task: {MAX_REPLAN_STEP} times. The task is not completed. Succeed: False"
                else:
                    error_msg += "\nNotice: Your code has been executed and the task is not completed. Please write code to complete the task from the current situation."
        print(error_msg)
        observation = error_msg + agent.report()
        if env.done:
            break
    
    is_success = env.reward
    consumed_tokens = Worker_agent.consumed_tokens()
    return is_success, cur_step, error_step, consumed_tokens