import os
import re
import json
from OpenAI_Agent_API import get_ChatGPT_Agent, process_respond
from env_history import Agent, get_object_with_id, find_object

class Reflection_Bank:
    def __init__(self, save_path):
        self.reflection_dict = {}
        self.save_path = os.path.join(save_path, "reflection_bank.json")

    def load(self, save_path):
        save_path=os.path.join(save_path, "reflection_bank.json")
        with open(save_path, 'r') as rf:
            self.reflection_dict = json.load(rf)
        
    def save(self):
        with open(self.save_path, 'w') as wf:
            json.dump(self.reflection_dict, wf, indent=4)

    def add_failure(self, task_name, failure_exp):
        if task_name in self.reflection_dict:
            self.reflection_dict[task_name].append(failure_exp)
        else:
            self.reflection_dict[task_name] = [failure_exp]

    def get_reflection(self, task_name):
        if task_name in self.reflection_dict:
            output = f"\nHere is an failure record from previous trails\n{'\n'.join(self.reflection_dict[task_name][-2:])}\nPlease also analyze the plan or mistakes in this failure record in your thoughts, and consider how you can avoid the same problems in the plans you are about to make."
        else:
            output = ""
        return output

MAX_REPLAN_STEP = 5 
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
        from prompts.base_examples import find_example, put_example
        worker_example = find_example if args.simple_example else put_example
        Worker_agent = get_ChatGPT_Agent(args.model_name, "worker", "./prompts/base_prompt.txt", args.assistant_api, example_list=[worker_example])

    # Get the prompt of rules and relevant skills
    local_vars = {'agent': agent, 'get_object_with_id': get_object_with_id, 'find_object': find_object, 're': re}
    rule_manager.define_functions_from_rules(local_vars)
    skill_string = skill_bank.get_relevant_skill(env.task_type, local_vars)
    observation = env.init_info
    observation = f"{rule_manager.rule_string()}\n{skill_string}\n{observation}"
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
        if env.done:
            break

    is_success = env.reward
    consumed_tokens = Worker_agent.consumed_tokens()
    return is_success, cur_step, consumed_tokens