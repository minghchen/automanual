import os
import sys
import gym
import shutil
import openai
import argparse
import openai
import random
from env_history import InteractEnv
from autobuild_utils import Rule_Manager, Skill_Bank
from main_test import CombinedLogger

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
openai.api_key = os.environ["OPENAI_API_KEY"]
openai.base_url = os.environ["OPENAI_BASE_URL"]

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--examine_tasks", type=str, default=None, help="The type of the examining task")
    parser.add_argument('--num_env_per_task', type=int, default=3, help="the number of samples per task type.")
    parser.add_argument("--run_name", type=str, default="test_run", help="The name of the run")
    parser.add_argument("--model_name", type=str, default='gpt-4-1106-preview', help="The LLM to use. One of 'gpt-4o', 'gpt-4-turbo', 'gpt-4-0125-preview', 'gpt-4-1106-preview', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-1106'")
    parser.add_argument('--assistant_api', action='store_true', help="use openai assistant api")
    parser.add_argument("--agent_type", type=str, default="replan", help="The type of the agent, prompt and examples")
    parser.add_argument("--simple_example", action='store_true', help="Use simplest example")
    parser.add_argument("--is_resume", action='store_true', help="To resume run")
    parser.add_argument("--start_round_id", type=int, default=0, help="If resume, the start round")
    parser.add_argument("--headless", action='store_true', help="using headless mode or not")
    args = parser.parse_args()
    return args

TASKS = [
    "search-engine",
    "tic-tac-toe",
    "email-inbox-forward-nl-turk",
    "terminal",
    "login-user-popup",
    "guess-number",
    "email-inbox-nl-turk"
]

def get_result_dict(rule_manager):
    '''get the results of each task type from the history in rule_manager'''
    num_successes = 0
    result_dict = {}
    for k, v in rule_manager.global_history.items():
        if "epoch_" in k:
            task_type = v["task_type"]
            num_successes += v["is_success"]
            if task_type not in result_dict:
                result_dict[task_type] = [v["error_step"] if v["is_success"] else -1]
            else:
                result_dict[task_type].append(v["error_step"] if v["is_success"] else -1)
    print(result_dict)
    return num_successes, result_dict

def main(args):
    print("Use Assistant_API:", args.assistant_api)
    logging_dir = args.run_name
    if args.agent_type == "autobuild_case":
        from autobuild_case_trail import run
    elif args.agent_type == "autobuild":
        from autobuild_trail import run
    elif args.agent_type == "autobuild_offline":
        from autobuild_offline import run
    else:
        raise ValueError(f"{args.agent_type} is invaild.")
    
    if args.simple_example:
        from prompts.autobuild_simple_examples import init_rules
    else:
        from prompts.autobuild_examples import init_rules

    rule_manager = Rule_Manager(init_rules=init_rules, save_path=logging_dir)
    skill_bank = Skill_Bank(save_path=logging_dir)

    if args.is_resume:
        # load environment configs
        rule_manager.load(save_path=logging_dir)
        skill_bank.load(save_path=logging_dir)
        epoch_id = rule_manager.cur_epoch
        if rule_manager.global_history[f"epoch_{epoch_id}"]['check_rule']:
            epoch_id += 1
        num_successes, result_dict = get_result_dict(rule_manager)
    else:
        # Create the run directory
        if os.path.exists(logging_dir):
            shutil.rmtree(logging_dir)
        os.makedirs(logging_dir)
        epoch_id = 0
        num_successes = 0
        result_dict = {}
    
    print(f"Sending all logs to: {logging_dir} (Run name). Start from round {args.start_round_id}.")
    # set paths to log files
    trial_log_path = os.path.join(logging_dir, 'trial.log')
    world_log_path = os.path.join(logging_dir, 'world.log')

    with open(world_log_path, 'a') as wf:
        wf.write(f'\n\n***** Start building *****\n\n')

    # run trials
    num_round = args.num_env_per_task // 3
    for round_id in range(args.start_round_id, num_round):
        print(f"round {round_id}", result_dict)
        for z, task_type in enumerate(TASKS):
            if args.examine_tasks is not None and all([(t not in task_type) for t in args.examine_tasks.split(",")]): continue
            for trial_idx in range(3):
                if round_id >= 1 and all(s >= 0 for s in result_dict[task_type][-3:]): continue
                print(f"starting epoch {epoch_id}: {task_type}")
                raw_env = gym.make("MiniWoBEnv-v0", env_name=task_type, headless=args.headless)
                ob = raw_env.reset(seeds=[random.random()], record_screenshots=False)

                env = InteractEnv(raw_env, z, task_type, epoch_id, ob)
                # run one trial
                with CombinedLogger(trial_log_path) as s:
                    while True:
                        try:
                            is_success, replan_step, error_step, consumed_tokens = run(args, env, rule_manager, skill_bank)
                        except Exception as e:
                            print(e)
                        else:
                            break
                raw_env.close()

                if is_success:
                    status_str = f'Epoch #{epoch_id}, Environment #{z}-{trial_idx}, {env.task}: SUCCESS, Replan_step: {replan_step}, Error_step: {error_step}'
                else:
                    status_str = f'Epoch #{epoch_id}, Environment #{z}-{trial_idx}, {env.task}: FAIL, Replan_step: {replan_step}, Error_step: {error_step}'
                epoch_id += 1
                
                # log to world log
                with open(world_log_path, 'a') as f:
                    f.write(status_str + '\n')
                    f.write(consumed_tokens)

                # log env results to trial log
                with open(trial_log_path, 'a') as wf:
                    wf.write(f'\n#####\n\n{status_str}\n\n#####\n')

                num_successes, result_dict = get_result_dict(rule_manager)

    # log trial results to trial and world logs
    log_str = f"""
***** End building *****
-----
SUCCESS: {num_successes}
TOTAL: {epoch_id}
ACCURACY: {round(num_successes / epoch_id, 2)}
-----"""
    log_str += f"""
Accuracy Per Task Type: {[f"{k}: {sum(1 for i in v if i >= 0)}/{len(v)}" for k,v in result_dict.items()]}
Error Step Per Task Type: {result_dict}
"""
    with open(world_log_path, 'a') as wf:
        wf.write(log_str + '\n')

if __name__ == '__main__':
    args = get_args()
    main(args)
