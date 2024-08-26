import re
from OpenAI_Agent_API import get_ChatGPT_Agent, process_respond
from prompts.autobuild_examples import formulater_example

def run_formulation(args, rule_manager):
    Formulater_agent = get_ChatGPT_Agent(args.model_name, "formulater", "./prompts/formulater_prompt.txt", args.assistant_api, example_list=[formulater_example])

    print(f"\nBegin formulating rules and generating the manual.\n")
    message = f"Print rule_manager.all_rules:\n{str(rule_manager.all_rules)}"
    respond = Formulater_agent.generate(message)
    print(respond)
    match = re.search(r"```markdown\n(.*?)\n```", respond, re.DOTALL)
    assert match is not None
    manual = match.group(1)

    rule_ids = re.findall(r'\*\*(rule_\d+)\*\*', manual)
    rule_ids = list(dict.fromkeys(rule_ids))
    assert len(rule_ids) == len(rule_manager.all_rules) # the manual includes all rules.

    new_all_rules = {f"rule_{new_i}": rule_manager.all_rules[old_i] for new_i, old_i in enumerate(rule_ids)}
    id_mapping = {old_i: f"rule_{new_i}" for new_i, old_i in enumerate(rule_ids)}
    for old_id, new_id in id_mapping.items():
        manual = re.sub(rf'\*\*{old_id}\*\*', new_id, manual)

    # Process the manual
    for rule_id in new_all_rules:
        assert rule_id in manual
        rule_dict = new_all_rules[rule_id]
        pattern = rf'({rule_id}):\s*[^.]*\.'
        new_description = f"**{rule_id} (type=\"{rule_dict['type']}\")**: {rule_dict['rule']}"
        if len(rule_dict['example'])>0:
            if rule_dict['example'].strip()[0] == "#":
                rule_dict['example'] = f"\n```python\n{rule_dict['example']}\n```"
            new_description += f" For example, {rule_dict['example']}"
        new_description += "\n"
        manual = re.sub(pattern, new_description, manual, count=1)

    manual = re.sub(r'\*\*', '', manual)

    rule_manager.all_rules = new_all_rules
    print(manual)
    rule_manager.manual = manual
    rule_manager.save()