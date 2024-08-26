import os
import sys
import json
import yaml
import shutil
import openai
import argparse
import importlib
import alfworld
import alfworld.agents.environment
from env_history import InteractEnv
from autobuild_utils import Rule_Manager, Skill_Bank

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
os.environ["ALFWORLD_DATA"] = "../alfworld/downloaded"
openai.api_key = os.environ["OPENAI_API_KEY"]
openai.base_url = os.environ["OPENAI_BASE_URL"]

ENV_NUM = 135

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--examine_tasks", type=str, default=None, help="The type of the examining task, 'pick_and_place', 'pick_clean_then_place', 'pick_heat_then_place', 'pick_cool_then_place', 'pick_two_obj', 'look_at_obj'")
    parser.add_argument('--num_env_per_task', type=int, default=3, help="the number of samples per task type.")
    parser.add_argument("--run_name", type=str, help="The name of the run")
    parser.add_argument("--model_name", type=str, default='gpt-4-1106-preview', help="The LLM to use. One of 'gpt-4o', 'gpt-4-turbo', 'gpt-4-0125-preview', 'gpt-4-1106-preview', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-1106', 'human'")
    parser.add_argument('--assistant_api', action='store_true', help="use openai assistant api")
    parser.add_argument("--agent_type", type=str, default="replan", help="The type of the agent, prompt and examples")
    parser.add_argument("--simple_example", action='store_true', help="Use simplest example")
    parser.add_argument('--mode', type=str, default="testing", help="the mode of autobuild: formulating, testing")
    parser.add_argument("--is_resume", action='store_true', help="To resume run")
    parser.add_argument("--start_env_id", type=int, default=0, help="If resume, the start env")
    args = parser.parse_args()
    return args

from io import StringIO
class CombinedLogger:
    def __init__(self, filename, stdout=None):
        self.file = open(filename, "a")
        self.terminal = sys.stdout
        self.stdout = stdout if stdout is not None else StringIO()

    def write(self, message):
        self.terminal.write(message)
        self.file.write(message)
        self.stdout.write(message)

    def flush(self):
        self.terminal.flush()
        self.file.flush()
        self.stdout.flush()

    def __enter__(self):
        sys.stdout = self
        return self.stdout

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.terminal
        self.file.close()

from test_trial import run
def main(args):
    print("Use Assistant_API:", args.assistant_api)
    logging_dir = args.run_name

    rule_manager = Rule_Manager({}, save_path=logging_dir)
    skill_bank = Skill_Bank(save_path=logging_dir)
    num_successes = 0
    test_result_dict = {}

    if "autobuild" in args.agent_type:
        # load environment configs
        rule_manager.load(save_path=logging_dir)
        skill_bank.load(save_path=logging_dir)
    elif not args.is_resume:
        # Create the run directory
        if os.path.exists(logging_dir):
            shutil.rmtree(logging_dir)
        os.makedirs(logging_dir)

    if args.mode=="formulating":
        from formulate_manual import run_formulation
        run_formulation(args, rule_manager)
        return

    if "autobuild" in args.agent_type:
        logging_dir = os.path.join(logging_dir, 'test')
        os.makedirs(logging_dir, exist_ok=True)
    
    print(f"Sending all logs to: {logging_dir} (Run name).")
    # set paths to log files
    world_log_path = os.path.join(logging_dir, 'world.log')
    trial_log_path = os.path.join(logging_dir, f'trial.log')

    with open(world_log_path, 'a') as wf:
        wf.write(f'\n\n***** Start testing *****\n\n')

    importlib.reload(alfworld)
    importlib.reload(alfworld.agents.environment)
    with open("base_config.yaml") as reader:
        config = yaml.safe_load(reader)
    raw_env = getattr(alfworld.agents.environment, config["env"]["type"])(config, train_eval="eval_out_of_distribution")
    raw_env = raw_env.init_env(batch_size=1)

    # run trials
    epoch_id = 0
    for z in range(ENV_NUM):
        # get the task and init info
        ob, info = raw_env.reset()
        ob = '\n'.join(ob[0].split('\n\n')[1:]).replace("put a clean", "put a cleaned")
        name = '/'.join(info['extra.gamefile'][0].split('/')[-3:-1])
        task_type = name.split("-")[0]
        print(f"using {name}, Environment {z}")
        if args.examine_tasks is not None and all([(t not in name) for t in args.examine_tasks.split(",")]): continue
        if z < args.start_env_id: continue
        if task_type in test_result_dict and len(test_result_dict[task_type]) >= args.num_env_per_task: continue
        print(f"starting epoch {epoch_id}")

        env = InteractEnv(raw_env, z, name, epoch_id, ob)
        # run trial
        with CombinedLogger(trial_log_path) as s:
            try:
                is_success, error_step, consumed_tokens = run(args, env, rule_manager, skill_bank)
            except Exception as e:
                print(e)
                continue

        if is_success:
            status_str = f'Epoch #{epoch_id}, Environment #{z}, {env.task}: SUCCESS, Error_step: {error_step}'
            num_successes += 1
        else:
            status_str = f'Epoch #{epoch_id}, Environment #{z}, {env.task}: FAIL, Error_step: {error_step}'
        epoch_id += 1

        # log to world log
        with open(world_log_path, 'a') as f:
            f.write(status_str + '\n')
            f.write(consumed_tokens)

        # log env results to trial log
        with open(trial_log_path, 'a') as wf:
            wf.write(f'\n#####\n\n{status_str}\n\n#####\n')

        if task_type not in test_result_dict:
            test_result_dict[task_type] = [error_step if is_success else -1]
        else:
            test_result_dict[task_type].append(error_step if is_success else -1)
            
        if all([len(v)>=args.num_env_per_task for v in test_result_dict.values()]): break
            

    # close environment object
    raw_env.close()

    # log trial results to world logs
    log_str = f"""
***** End testing *****
-----
SUCCESS: {num_successes}
TOTAL: {epoch_id}
ACCURACY: {round(num_successes / epoch_id, 2)}
-----"""
    log_str += f"""
Accuracy Per Task Type: {[f"{k}: {sum(1 for i in v if i >= 0)}/{len(v)}" for k,v in test_result_dict.items()]}
Error Step Per Task Type: {test_result_dict}
"""
    with open(world_log_path, 'a') as wf:
        wf.write(log_str + '\n')

if __name__ == '__main__':
    args = get_args()
    main(args)
