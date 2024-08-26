from OpenAI_Agent_API import get_ChatGPT_Agent, process_respond
from prompts.base_examples import enter_example, search_example
from autobuild_trail import run_trail

def run(args, env, rule_manager, skill_bank):
    epoch_id = f"epoch_{env.epoch_id}"
    worker_example = enter_example if args.simple_example else search_example
    Worker_agent = get_ChatGPT_Agent(args.model_name, "worker", "./prompts/base_prompt.txt", args.assistant_api, example_list=[worker_example])

    if epoch_id not in rule_manager.global_history:
        run_trail(args, env, rule_manager, skill_bank, Worker_agent)

    epoch_data = rule_manager.global_history[epoch_id]
    is_success = epoch_data["is_success"]
    replan_step = epoch_data["replan_step"]
    error_step = epoch_data["error_step"]

    consumed_tokens = Worker_agent.consumed_tokens()
    return is_success, replan_step, error_step, consumed_tokens

from prompts.autobuild_examples import *
from prompts.builder_case_prompt import *
from autobuild_case_trail import run_autobuild_case, run_merge
MAX_RULE_NUM = 12
def run_buildoffline(args, rule_manager):
    print("\nBegin extracting rules from the history.\n")
    Builder_agent = get_ChatGPT_Agent(args.model_name, "builder", "./prompts/builder_base_prompt.txt", args.assistant_api, example_list=[builder_example])

    epoch_ids = [k for k in rule_manager.global_history if "epoch_" in k]
    consumed_tokens = ""
    for epoch_id in epoch_ids:
        epoch_data = rule_manager.global_history[epoch_id]
        interact_history = epoch_data["interact_history"]
        is_success = epoch_data["is_success"]
        error_step = epoch_data["error_step"]
        if len(str(interact_history)) > 11000:
            print("The interact_history is too long to process.")
            continue
        if not rule_manager.global_history[epoch_id]['check_rule']:
            run_autobuild_case(interact_history, is_success, error_step, rule_manager, Builder_agent)
            rule_manager.global_history[epoch_id]['check_rule'] = True
            rule_manager.save()

        consumed_tokens += Builder_agent.consumed_tokens()
        consumed_tokens = run_merge(args, rule_manager, consumed_tokens)
    
    return consumed_tokens