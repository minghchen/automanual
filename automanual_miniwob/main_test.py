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

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
openai.api_key = os.environ["OPENAI_API_KEY"]
openai.base_url = os.environ["OPENAI_BASE_URL"]

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--examine_tasks", type=str, default=None, help="The type of the examining task")
    parser.add_argument('--num_env_per_task', type=int, default=3, help="the number of samples per task type.")
    parser.add_argument("--run_name", type=str, default="test_run", help="The name of the run")
    parser.add_argument("--model_name", type=str, default='gpt-4-1106-preview', help="The LLM to use. One of 'gpt-4o', 'gpt-4-turbo', 'gpt-4-0125-preview', 'gpt-4-1106-preview', 'gpt-3.5-turbo-0125', 'gpt-3.5-turbo-1106', 'human'")
    parser.add_argument('--assistant_api', action='store_true', help="use openai assistant api")
    parser.add_argument("--agent_type", type=str, default="replan", help="The type of the agent, prompt and examples")
    parser.add_argument("--simple_example", action='store_true', help="Use simplest example")
    parser.add_argument('--mode', type=str, default="building", help="the mode of autobuild: building, formulating, testing")
    parser.add_argument("--is_resume", action='store_true', help="To resume run")
    parser.add_argument("--start_epoch_id", type=int, default=0, help="If resume, the start epoch")
    parser.add_argument("--headless", action='store_true', help="using headless mode or not")
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

TASKS_FEEDBACK = [
    "search-engine",
    "tic-tac-toe",
    "email-inbox-forward-nl-turk",
    "terminal",
    "login-user-popup",
    "guess-number",
    "email-inbox-nl-turk",
    "email-inbox-forward-nl",
    "email-inbox"
]

ALL_TASKS = ['choose-list', 'click-button', 'click-button-sequence', 'click-checkboxes', 'click-checkboxes-large', 'click-checkboxes-soft', 'click-checkboxes-transfer', 'click-collapsible', 'click-collapsible-2', 'click-color', 'click-dialog', 'click-dialog-2', 'click-link', 'click-menu', 'click-option', 'click-scroll-list', 'click-shades', 'click-shape', 'click-tab', 'click-tab-2', 'click-tab-2-hard', 'click-test', 'click-test-2', 'click-widget', 'count-shape', 'enter-date', 'enter-password', 'enter-text', 'enter-text-dynamic', 'enter-time', 'focus-text', 'focus-text-2', 'grid-coordinate', 'identify-shape', 'login-user', 'multi-layouts', 'multi-orderings', 'navigate-tree', 'simple-algebra', 'social-media', 'social-media-all', 'social-media-some', 'use-autocomplete', 'use-spinner', 'guess-number', 'login-user-popup', 'tic-tac-toe', 'search-engine', 'terminal', 'email-inbox', 'email-inbox-nl-turk', 'email-inbox-forward-nl', 'email-inbox-forward-nl-turk']

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

    print(f"Sending all logs to: {logging_dir} (Run name). Start from epoch {args.start_epoch_id}.")
    # set paths to log files
    trial_log_path = os.path.join(logging_dir, 'trial.log')
    world_log_path = os.path.join(logging_dir, 'world.log')

    with open(world_log_path, 'a') as wf:
        wf.write(f'\n\n***** Start testing *****\n\n')

    # run trials
    epoch_id = 0
    tasks_with_feedback = TASKS_FEEDBACK # ALL_TASKS
    for z, task_type in enumerate(tasks_with_feedback):
        if args.examine_tasks is not None and all([(t not in task_type) for t in args.examine_tasks.split(",")]): continue
        for trial_idx in range(args.num_env_per_task):
            if epoch_id < args.start_epoch_id:
                epoch_id += 1
                continue
            print(f"starting epoch {epoch_id}: {task_type}")
            raw_env = gym.make("MiniWoBEnv-v0", env_name=task_type, headless=args.headless)
            ob = raw_env.reset(seeds=[random.random()], record_screenshots=False)

            env = InteractEnv(raw_env, z, task_type, epoch_id, ob)
            # run trial
            with CombinedLogger(trial_log_path) as s:
                try:
                    is_success, replan_step, error_step, consumed_tokens = run(args, env, rule_manager, skill_bank)
                except Exception as e:
                    print(e)
                    is_success, error_step, consumed_tokens = False, -1, ""
                    break

            if is_success:
                status_str = f'Epoch #{epoch_id}, Environment #{z}-{trial_idx}, {env.task}: SUCCESS, Replan_step: {replan_step}, Error_step: {error_step}'
                num_successes += 1
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
            
            raw_env.close()

            if task_type not in test_result_dict:
                test_result_dict[task_type] = [error_step if is_success else -1]
            else:
                test_result_dict[task_type].append(error_step if is_success else -1)

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
    main(args)
