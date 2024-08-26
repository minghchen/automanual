import re
import json
from browser_env import ActionTypes, action2str, create_stop_action
from browser_env.actions import create_id_based_action, create_none_action, ActionParsingError
from evaluation_harness import evaluator_router

import os
AWS_HOSTNAME = os.environ["AWS_HOSTNAME"]
URL_to_SITE = {
    f"http://{AWS_HOSTNAME}:7770": "SHOPPING",
    f"http://{AWS_HOSTNAME}:7780/admin": "SHOPPING_ADMIN",
    f"http://{AWS_HOSTNAME}:9999": "REDDIT", 
    f"http://{AWS_HOSTNAME}:8023": "GITLAB",
    f"http://{AWS_HOSTNAME}:3000": "MAP",
    f"http://{AWS_HOSTNAME}:8888": "WIKIPEDIA",
    f"http://{AWS_HOSTNAME}:4399": "HOMEPAGE"
}

class Agent:
    # The Agent class is responsible for processing the pythonic actions output by the LLM, 
    # passing them to the InteractEnv. It gets the result of the action from the environment 
    # (success or failure information), the new observation and whether it is completed or not. 
    # It is also responsible for reporting the results of these executions to the LLM.

    def __init__(self, env):
        self.env = env
        self.cur_obs = self.last_obs = env.cur_obs
        self.cur_obs_dict = self.last_obs_dict = env.cur_obs_dict # the current accessibility tree mapping ids to their text
        self.cur_url = env.cur_url
        self.is_success = False
        self.last_report_step = 0

    # Get an observation from the environment after performing an action
    def observation(self, action_str, script):
        if self.env.done:
            raise ValueError("This epoch is done.")
        try:
            action_info = self.env.step(action_str, script)
            self.cur_obs = self.env.cur_obs
            self.cur_obs_dict = self.env.cur_obs_dict
            self.cur_url = self.env.cur_url
            self.cur_site = self.env.cur_site
        except ActionParsingError as e:
            raise ValueError(f"Invalid action: agent.{action_str}")
        if "Please check" in action_info:
            raise ValueError(f"Error: {action_info}")
        return self.cur_obs_dict
    
    # Here are the admissible actions:
    ### Page Operation Actions:
    # clicks on an element with a specific id on the webpage. If the element has popup options, input the option to select one
    def click(self, id: int, option=""):
        if option:
            return self.observation(f"click({id}, \"{option}\")", f"select [{id}] [{option}]")
        else:
            return self.observation(f"click({id})", f"click [{id}]")
    
    # type the content into the field with id. By default, the existing content in the field will be cleared unless clear_existing is set to False, and the "Enter" key is pressed after typing unless press_enter_after is set to False
    def type(self, id: int, content: str, clear_existing=True, press_enter_after=True):
        return self.observation(f"type({id},\"{content}\",\"{clear_existing}\",\"{press_enter_after}\")", f"type [{id}] [{content}] [{int(clear_existing)}] [{int(press_enter_after)}]")
    
    # hover over an element with id
    def hover(self, id: int):
        return self.observation(f"hover({id})", f"hover [{id}]")
    
    # simulates the pressing of a key combination on the keyboard (e.g., Ctrl+v)
    def press(self, key_comb: str):
        return self.observation(f"press(\"{key_comb}\")", f"press [{key_comb}]")
    
    # scroll the page up or down.
    def scroll(self, direction: str="down"):
        return self.observation(f"scroll(\"{direction}\")", f"scroll [{direction}]")
    
    ### Tab Management Actions:
    # open a new, empty browser tab
    def new_tab(self):
        return self.observation("new_tab()", "new_tab")
        
    # switch the browser's focus to a specific tab using its index
    def tab_focus(self, tab_index: int):
        return self.observation(f"tab_focus({tab_index})", f"tab_focus [{tab_index}]")

    # close the currently active tab.
    def close_tab(self):
        return self.observation("close_tab()", "close_tab")
    
    ### URL Navigation Actions:
    # navigate to a specific URL
    def goto(self, url: str):
        return self.observation(f"goto(\"{url}\")", f"goto [{url}]")
    
    # navigate to the previously viewed page
    def go_back(self):
        return self.observation("go_back()", "go_back")
    
    # navigate to the next page (if a previous 'go_back' action was performed).
    def go_forward(self):
        return self.observation("go_forward()", "go_forward")

    ### Completion Action:
    # Issue this action when you believe the task is complete. If the objective is to find a text-based answer, provide the answer in the bracket. If you believe the task is impossible to complete, provide the answer="N/A" in the bracket.
    def stop(self, answer: str=""):
        return self.observation(f"stop(\"{answer}\")", f"stop [{answer}]")

    # Report agent's executed actions.
    def report_action_history(self, error_msg=""):
        msg = f""
        for k, v in self.env.env_history.items():
            if int(k.split("obs_")[-1]) > self.last_report_step:
                msg += f"{k}: {v}\n"
        if error_msg:
            msg += error_msg
        self.last_report_step = self.env.action_step
        return msg

    # Report agent's current observation.
    def report(self):
        msg = ""
        if self.last_obs_dict != self.cur_obs_dict:
            msg += f"\nOBSERVATION:\n{self.cur_obs}\nCurrent URL of Simulated {self.cur_site}: {self.cur_url}\n"
            self.last_obs = self.cur_obs
            self.last_obs_dict = self.cur_obs_dict
        return msg

RATE_LIMIT_TXT = "StaticText 'You cannot post more. Wait a while before trying again.'"
class PostRateLimit(Exception):
    """Exception raised when the rate limit of submitting posts is exceeded."""
    def __init__(self, message="Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)

EXTRA_TXT = "The information in this tab has been changed. This tab contains invalid data. Please resolve this before saving."
MAX_ACTION_STEP = 50
class InteractEnv:
    # The InteractEnv class wraps the raw environment: 
    # It is responsible for converting actions to actions executable in the raw environment and capturing
    # post-execution observations and errors (including action conversion errors, action object errors, 
    # environment execution errors, etc.) or action success results, providing this information to the Agent. 
    # Then it detects whether the environment terminates (the raw environment terminated, maximum number of action 
    # steps reached, LLM actively terminated) and calculate the reward.
    # It will also record interactions between Agent and the environment, which can be used for reporting to LLM.
    
    def __init__(self, raw_env, config_file, epoch_id, task, task_type, render_helper):
        self._env = raw_env
        self.config_file = config_file
        self.epoch_id = epoch_id
        self.task = task
        self.task_type = task_type
        self.render_helper = render_helper
        self.reset()
        
        self.cur_obs = self.init_obs = self.state_info["observation"]["text"].replace(EXTRA_TXT, "")
        self.cur_obs_dict = self.get_obs_dict(self.state_info["info"])
        self.cur_url = self.state_info["info"]["page"].url
        self.cur_site = get_cur_site(self.cur_url)
        self.init_info = f"\nHere is the task: {task}\nOBSERVATION:\n{self.cur_obs}\nCurrent URL of Simulated {self.cur_site}: {self.cur_url}\n"
        self.action_step = 0
        self.env_history = {"obs_0": f"\nHere is the task: {task}\nOBSERVATION:...\nCurrent URL of Simulated {self.cur_site}: {self.cur_url}\n"}
        self.evaluator = evaluator_router(config_file)
        self.meta_data = {"action_history": ["None"]}
        self.answer_action = create_stop_action("")
        self.done = False
        self.reward = False

    def reset(self):
        obs, info = self._env.reset(options={"config_file": self.config_file})
        obs, _, _, _, info = self._env.step(create_none_action()) # ensure the page is refreshed
        self.state_info = {"observation": obs, "info": info}
    
    def step(self, action_str, script):
        action = create_id_based_action(script)
        self.cur_script, self.cur_action = script, action
        action_info = get_action_description(action, self.state_info["info"]["observation_metadata"])
        
        obs, _, self.done, _, info = self._env.step(action)
        obs, _, self.done, _, info = self._env.step(create_none_action()) # ensure that the action is complete and the page is refreshed
        self.state_info = {"observation": obs, "info": info}
        self.cur_obs = self.state_info["observation"]["text"].replace(EXTRA_TXT, "")
        self.cur_obs_dict = self.get_obs_dict(self.state_info["info"])
        self.cur_url = self.state_info["info"]["page"].url
        self.cur_site = get_cur_site(self.cur_url)

        self.action_step += 1
        obs_id = f"obs_{self.action_step}"
        self.env_history[obs_id] = f"Act: agent.{action_str}. Obs: {action_info}"
        # When the stop action is generated, evaluate the reward and send the feedback
        if action["action_type"] == ActionTypes.STOP:
            self.done = True
            self.answer_action = action
        elif self.action_step >= MAX_ACTION_STEP:
            self.done = True
            self.env_history[obs_id] += f" The agent has performed too many actions, exceeding the number of steps allowed to complete the task: {MAX_ACTION_STEP} steps." 
        if self.done:
            self.reward = bool(self.evaluator(
                trajectory=[self.answer_action],
                config_file=self.config_file,
                page=self._env.page,
                client=self._env.get_page_client(self._env.page)))
            with open(self.config_file, "r") as f:
                configs = json.load(f)
                eval_types = configs["eval"]["eval_types"]
            feedback = f"Success: {self.reward}"
            # The feedback for url_match. Since some tasks require matching URL instead of giving answer, this needs to be clarified to the agent.
            if eval_types == ["url_match"] and not self.reward:
                feedback += "; You are not stopping at the required web page."
            self.env_history[obs_id] += f" This epoch is done. {feedback}"
        return action_info
    
    def save_render(self, response):
        self.cur_action['raw_prediction'] = response
        self.render_helper.render(self.cur_action, self.state_info, self.meta_data, render_screenshot=True)
        self.meta_data["action_history"].append(self.cur_script)
    
    def get_obs_dict(self, info):
        obs_nodes_info = info["observation_metadata"]["text"]["obs_nodes_info"]
        obs_dict = {int(k): re.sub(r'^\[\d+\]\s*', '', v['text'].replace(EXTRA_TXT, "")) for k,v in obs_nodes_info.items()}
        return obs_dict
    
def get_cur_site(url):
    for url_root, site in URL_to_SITE.items():
        if url_root in url:
            return site

def get_action_description(action, observation_metadata, action_set_tag="id_accessibility_tree"):
    """Generate the text version of the predicted actions to store in action history for prompt use.
    May contain hint information to recover from the failures"""

    text_meta_data = observation_metadata["text"]["obs_nodes_info"]
    if action["action_type"] in [ActionTypes.CLICK, ActionTypes.HOVER, ActionTypes.TYPE, ActionTypes.SELECT_OPTION]:
        action_name = str(action["action_type"]).split(".")[1].lower()
        if action["element_id"] in text_meta_data:
            node_content = text_meta_data[action["element_id"]]["text"]
            node_content = " ".join(node_content.split()[1:])
            action_str = action2str(action, action_set_tag, node_content)
            if node_content.startswith("checkbox"):
                action_str += " Notice: You cannot click a checkbox element, and you should click the StaticText above it instead."
        else:
            action_str = f"Attempt to perfom \"{action_name}\" on element \"[{action['element_id']}]\" but no matching element found. Please check the observation more carefully."
    else:
        action_str = "Action has been performed."

    return action_str