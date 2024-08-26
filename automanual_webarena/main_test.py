import os
import sys
import json
import shutil
import openai
import argparse
import openai
import random
import tempfile
import subprocess

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
openai.api_key = os.environ["OPENAI_API_KEY"]
openai.base_url = os.environ["OPENAI_BASE_URL"]

# set the URLs of each website
AWS_HOSTNAME = os.environ["AWS_HOSTNAME"]
os.environ["SHOPPING"] = f"http://{AWS_HOSTNAME}:7770"
os.environ["SHOPPING_ADMIN"] = f"http://{AWS_HOSTNAME}:7780/admin"
os.environ["REDDIT"] = f"http://{AWS_HOSTNAME}:9999"
os.environ["GITLAB"] = f"http://{AWS_HOSTNAME}:8023"
os.environ["MAP"] = f"http://{AWS_HOSTNAME}:3000"
os.environ["WIKIPEDIA"] = f"http://{AWS_HOSTNAME}:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing"
os.environ["HOMEPAGE"] = f"http://{AWS_HOSTNAME}:4399"
print("Done setting up URLs")

# First, run `python scripts/generate_test_data.py` to generate the config files
p = subprocess.run(["python", "../webarena/scripts/generate_test_data.py"], capture_output=True)
# It will generate individual config file for each test example in config_files
assert os.path.exists("config_files/0.json")

# re-validate login information
subprocess.run(["python", "../webarena/browser_env/auto_login.py"])
print("Done saving account cookies")

from browser_env import ScriptBrowserEnv
from browser_env.auto_login import get_site_comb_from_filepath
from browser_env.helper_functions import RenderHelper
from env_history import InteractEnv
from autobuild_utils import Rule_Manager, Skill_Bank

ENV_NUM = 812

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_name", type=str, default="test_run", help="The name of the run")
    parser.add_argument("--examine_sites", type=str, default=None, help="The sites for examining")
    parser.add_argument('--num_env_per_task', type=int, default=7, help="the number of samples per task type.")
    parser.add_argument("--model_name", type=str, default='gpt-4-1106-preview', help="The LLM to use. One of 'gpt-4o', 'gpt-4-turbo', 'gpt-4-0125-preview', 'gpt-4-1106-preview', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-1106', 'human'")
    parser.add_argument('--assistant_api', action='store_true', help="use openai assistant api")
    parser.add_argument("--agent_type", type=str, default="replan", help="The type of the agent, prompt and examples")
    # parser.add_argument("--simple_example", action='store_true', help="Use simplest example")
    parser.add_argument("--reflection", action='store_true', help="performing reflection or not")
    parser.add_argument('--mode', type=str, default="testing", help="the mode of autobuild: formulating, testing")
    parser.add_argument("--is_resume", action='store_true', help="To resume run")
    parser.add_argument("--start_env_id", type=int, default=0, help="If resume, the start env")
    parser.add_argument("--split", type=int, default=None, help="The x-th split of the examine site")
    parser.add_argument("--headless", action='store_true', help="using headless mode or not")
    parser.add_argument("--slow_mo", type=int, default=0, help="Slow down the browser by the specified amount")
    parser.add_argument("--sleep_after_execution", type=float, default=0.0)
    parser.add_argument("--action_set_tag", default="id_accessibility_tree", help="Action type")
    parser.add_argument("--observation_type", choices=["accessibility_tree", "html", "image"], default="accessibility_tree", help="Observation type")
    parser.add_argument("--result_dir", type=str, default="")
    parser.add_argument("--save_trace_enabled", action="store_true")
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

env_splits = {
    "reddit": [620],
    "shopping_admin": [158, 458, 552],
    "shopping": [168, 287, 377, 516],
    "map": [84, 253],
    "gitlab": [298, 418, 571]
}

from test_trial import run
def main(args):
    print("Use Assistant_API:", args.assistant_api)
    logging_dir = args.run_name
    
    rule_manager = Rule_Manager(init_rules={}, save_path=logging_dir)
    skill_bank = Skill_Bank(save_path=logging_dir)
    num_successes = 0
    test_result_dict = {}

    if "autobuild" in args.agent_type:
        # load environment configs
        rule_manager.load(save_path=logging_dir)
        skill_bank.load(save_path=logging_dir)

    if args.mode=="formulating":
        from formulate_manual import run_formulation
        run_formulation(args, rule_manager)
        return
    
    if "autobuild" in args.agent_type:
        logging_dir = os.path.join(logging_dir, 'test')
        os.makedirs(logging_dir, exist_ok=True)

    print(f"Sending all logs to: {logging_dir} (Run name). Start from task_id: {args.start_env_id}.")
    # set paths to log files
    trial_log_path = os.path.join(logging_dir, 'trial.log')
    world_log_path = os.path.join(logging_dir, 'world.log')

    with open(world_log_path, 'a') as wf:
        wf.write(f'\n***** Start testing *****\n')

    raw_env = ScriptBrowserEnv(
        headless=args.headless,
        slow_mo=args.slow_mo,
        observation_type=args.observation_type,
        current_viewport_only=True,
        viewport_size={"width": 1280,"height": 960},
        save_trace_enabled=True,
        sleep_after_execution=args.sleep_after_execution,
    )

    # run trials
    epoch_id = 0
    for z in range(args.min_env, args.max_env):
        # get the task (intent)
        config_file = f"config_files/{z}.json"
        with open(config_file) as f:
            _c = json.load(f)
            task_id = _c["task_id"]
            sites = _c["sites"]
            task = _c["intent"]
            task_type = _c["intent_template"]
        
        if z < args.start_env_id: continue
        if args.examine_sites is not None and any([(site not in args.examine_sites.split(",")) for site in sites]): continue

        # automatically login
        if _c["storage_state"]:
            cookie_file_name = os.path.basename(_c["storage_state"])
            comb = get_site_comb_from_filepath(cookie_file_name)
            temp_dir = tempfile.mkdtemp()
            # subprocess to renew the cookie
            subprocess.run(["python", "../webarena/browser_env/auto_login.py", "--auth_folder", temp_dir, "--site_list", *comb])
            _c["storage_state"] = f"{temp_dir}/{cookie_file_name}"
            assert os.path.exists(_c["storage_state"])
            # update the config file
            config_file = f"{temp_dir}/{os.path.basename(config_file)}"
            with open(config_file, "w") as f:
                json.dump(_c, f)

        print(f"[Config file]: {config_file}\n[Task_id]: {task_id}")
        print(f"[Sites]: {','.join(sites)}\n[Intent]: {task} ({task_type})")

        render_helper = RenderHelper(config_file, args.result_dir, args.action_set_tag)
        env = InteractEnv(raw_env, config_file, epoch_id, task, task_type, render_helper)
        # run trial
        with CombinedLogger(trial_log_path) as s:
            is_success, replan_step, error_step, consumed_tokens = run(args, env, rule_manager, skill_bank)
        render_helper.close()

        if is_success:
            status_str = f'Epoch #{epoch_id}, Environment #{z}, {task}: SUCCESS, Replan_step: {replan_step}, Error_step: {error_step}'
            num_successes += 1
        else:
            status_str = f'Epoch #{epoch_id}, Environment #{z}, {task}: FAIL, Replan_step: {replan_step}, Error_step: {error_step}'
        epoch_id += 1
        
        # log to world log
        with open(world_log_path, 'a') as f:
            f.write(status_str + '\n')
            f.write(consumed_tokens)

        # log env results to trial log
        with open(trial_log_path, 'a') as wf:
            wf.write(f'\n#####\n\n{status_str}\n\n#####\n')

        if args.save_trace_enabled:
            raw_env.save_trace(os.path.join(args.result_dir, "traces", f"{task_id}.zip"))
            
        if task_type not in test_result_dict:
            test_result_dict[task_type] = [error_step if is_success else -1]
        else:
            test_result_dict[task_type].append(error_step if is_success else -1)

    # close environment object
    raw_env.close()

    # log trial results to trial and world logs
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
    # Select task_id interval based on the split
    if args.split is not None:
        env_split = [0] + env_splits[args.examine_sites] + [ENV_NUM]
        assert args.split < len(env_split)
        args.min_env, args.max_env = env_split[args.split-1], env_split[args.split]
        print(f"### {args.split}-th split of \"{args.examine_sites}\" site, ranging from {args.min_env} to {args.max_env} ###")
    else:
        args.min_env, args.max_env = 0, ENV_NUM

    logging_dir = args.run_name
    if not args.is_resume:
        # Create the run directory
        if os.path.exists(logging_dir):
            shutil.rmtree(logging_dir)
        os.makedirs(logging_dir)

    # Create the result directory recording traces
    if not args.result_dir:
        args.result_dir = os.path.join(logging_dir, "results")
    os.makedirs(args.result_dir, exist_ok=True)
    if args.save_trace_enabled:
        os.makedirs(os.path.join(args.result_dir, "traces"), exist_ok=True)

    main(args)
