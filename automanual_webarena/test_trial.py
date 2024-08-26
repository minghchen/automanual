import re
from env_history import Agent
from OpenAI_Agent_API import get_ChatGPT_Agent, process_respond
from prompts.examples import load_examples
from prompts.builder_case_prompt import worker_reflection_prompt

MAX_REPLAN_STEP = 25
def run(args, env, rule_manager, skill_bank):
    agent = Agent(env)

    # Create the Planner Agent and load the demonstration
    worker_example = load_examples(args.examine_sites).worker_example
    if "autobuild" in args.agent_type:
        Worker_agent = get_ChatGPT_Agent(args.model_name, "worker", "./prompts/worker_prompt.txt", False, example_list=[worker_example])
    else:
        worker_example = worker_example.replace("\n### Rules to consider: ...","")
        Worker_agent = get_ChatGPT_Agent(args.model_name, "worker", "./prompts/base_prompt.txt", False, example_list=[worker_example])

    # Get the prompt of rules and relevant skills
    local_vars = {'agent': agent, 're': re}
    rule_manager.define_functions_from_rules(local_vars)
    skill_string = skill_bank.get_relevant_skill(env.task_type, local_vars)
    observation = env.init_info
    observation = f"{rule_manager.rule_string()}\n{skill_string}\n{observation}"
    error_step = 0
    print(observation)
    # The Planner Agent starts trying to complete the current task
    for cur_step in range(MAX_REPLAN_STEP):
        respond = Worker_agent.generate(observation)
        if args.model_name == "human":
            respond_thought, respond_code = "human", respond
        else:
            print(respond)
            respond_thought, respond_code = process_respond(respond)
        # execute the solution code
        try:
            exec(respond_code, local_vars, local_vars)
        except Exception as e:
            if env.done and env.reward:
                error_msg = agent.report_action_history()
            else:
                error_msg = agent.report_action_history(error_msg=f"Execution error:\n{str(e)}\n")
                if "Timeout" not in error_msg: error_step += 1
        else:
            error_msg = agent.report_action_history()
            if not env.done:
                if cur_step==MAX_REPLAN_STEP-1:
                    error_msg += f"You have responded too many times, exceeding the number of response allowed to complete the task: {MAX_REPLAN_STEP} times. The task is not completed. Succeed: False"
                else:
                    error_msg += "\nNotice: Your code has been executed and the task is not completed. Please write code to complete the task from the current situation."
        
        observation = error_msg + agent.report()
        if args.model_name == "human":
            print(error_msg)
        else:
            print(observation)
            # Omit old OBSERVATION when input new OBSERVATION to save context
            if "OBSERVATION" in observation and not args.assistant_api:
                Worker_agent.messages[-2]['content'] = re.sub(r'OBSERVATION:.*', 'OBSERVATION:...', Worker_agent.messages[-2]['content'], flags=re.S)
            Worker_agent.messages[-2]['content'] = re.sub(r'Notice:.*', '', Worker_agent.messages[-2]['content'])
        
        env.save_render(respond_thought)
        if env.done:
            break
    
    is_success = env.reward
    # Generate the reflection
    if not is_success and args.reflection:
        respond = Worker_agent.generate(observation+worker_reflection_prompt)
        print(respond)
    consumed_tokens = Worker_agent.consumed_tokens()
    return is_success, cur_step, error_step, consumed_tokens