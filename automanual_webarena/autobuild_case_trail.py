from OpenAI_Agent_API import get_ChatGPT_Agent, process_respond
from prompts.examples import load_examples
from prompts.builder_case_prompt import *
from autobuild_trail import run_trail, run_merge

MAX_RULE_NUM = 15
def run(args, env, rule_manager, skill_bank):
    epoch_id = f"epoch_{env.epoch_id}"

    # Create the Planner and Builder Agent
    module = load_examples(args.examine_sites)
    worker_example = module.worker_example
    builder_example = module.builder_example
    Worker_agent = get_ChatGPT_Agent(args.model_name, "worker", "./prompts/worker_prompt.txt", args.assistant_api, example_list=[worker_example])
    Builder_agent = get_ChatGPT_Agent(args.model_name, "builder", "./prompts/builder_base_prompt.txt", args.assistant_api, example_list=[builder_example])

    # Get the trajectory of current epoch
    if epoch_id not in rule_manager.global_history:
        run_trail(args, env, rule_manager, skill_bank, Worker_agent)

    epoch_data = rule_manager.global_history[epoch_id]
    interact_history = epoch_data["interact_history"]
    is_success = epoch_data["is_success"]
    replan_step = epoch_data["replan_step"]
    error_step = epoch_data["error_step"]
    
    # The Builder Agent manages rules based on the current trajectory
    if not rule_manager.global_history[epoch_id]['check_rule']:
        run_autobuild_case(interact_history, is_success, error_step, rule_manager, Builder_agent)
        rule_manager.global_history[epoch_id]['check_rule'] = True
        rule_manager.save()

    consumed_tokens = Worker_agent.consumed_tokens() + Builder_agent.consumed_tokens()

    # If the rule number exceed the maximum, the Consolidator Agent merges or delete rules
    consumed_tokens = run_merge(args, rule_manager, consumed_tokens)
    
    return is_success, replan_step, error_step, consumed_tokens

def run_autobuild_case(interact_history, is_success, error_step, rule_manager, Builder_agent):
    direct_success = (is_success and error_step == 0)
    indirect_success = (is_success and error_step >= 1)

    print("\nBegin analyzing and extracting rules from the current epoch.\n")
    Builder_agent.add_prompt(f"Print rule_manager.all_rules:\n{str(rule_manager.all_rules)}\n")
    message = f"Current epoch's trajectory:\n{interact_history}\n"

    # The builder determine the case of the result and receive the corresponding prompt
    if direct_success:
        message += builder_success_prompt
    elif indirect_success:
        message += indirect_case_classify_prompt
        case_respond = Builder_agent.generate(message)
        print(case_respond)
        if "imperfect rules" in case_respond.lower():
            message = builder_indirect_case1_prompt
        else:
            message = builder_indirect_case2_prompt
    else:
        message += failure_case_classify_prompt
        case_respond = Builder_agent.generate(message)
        print(case_respond)
        if "imperfect rules" in case_respond.lower():
            message = builder_failure_case1_prompt
        else:
            message = builder_failure_case2_prompt
    print(f"\nBegin managing rules from the current epoch.\n")
    respond = Builder_agent.generate(message)
    print(respond)
    respond_thought, respond_code = process_respond(respond)
    # execute the solution code
    exec(respond_code)
    message = rule_manager.report()