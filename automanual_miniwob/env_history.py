import re
import logging

logging.basicConfig(level=logging.WARNING)

import urllib3
urllib3.disable_warnings()
from selenium.webdriver.common.keys import Keys
from computergym.miniwob.miniwob_interface.action import (
    MiniWoBType,
    MiniWoBElementClickId,
    MiniWoBElementClickXpath,
    MiniWoBElementClickOption,
    MiniWoBMoveXpath,
)

class Agent:
    # The Agent class is responsible for processing the pythonic actions output by the LLM, 
    # passing them to the InteractEnv. It gets the result of the action from the environment 
    # (success or failure information), the new observation and whether it is completed or not. 
    # It is also responsible for reporting the results of these executions to the LLM.

    def __init__(self, env):
        self.env = env
        self.cur_html_string = env.init_obs
        self.is_success = False
        self.last_report_step = 0
        self.last_html_string = env.init_obs

    # Get an observation from the environment after performing an action
    def observation(self, action):
        if self.env.done:
            raise ValueError("This epoch is done.")
        run_info = self.env.step(action)
        self.cur_html_string = self.env.cur_obs
        if "Action done" not in run_info:
            raise ValueError(run_info)
        return self.cur_html_string
    
    # Here are the admissible actions:
    # Action: type a string into the input box
    # this function returns the html after the action
    def type(self, characters: str):
        return self.observation(f"type(\"{characters}\")")

    # Actions: press a key on the keyboard, the input can be one of the following:
    # enter, space, arrow_left, arrow_right, arrow_up, arrow_down, backspace
    # this function returns the html after the action
    def press_key(self, key: str):
        return self.observation(f"press_key(\"{key}\")")
        
    # Action: click an option HTML element in a list with an XPath
    # this function returns the html after the action
    def click_option(self, xpath: str):
        return self.observation(f"click_option(\"{xpath}\")")

    # Action: click an HTML element with an XPath
    # this function returns the html after the action
    def click_xpath(self, xpath: str):
        return self.observation(f"click_xpath(\"{xpath}\")")

    # Action: move the mouse cursor on an HTML element with an XPath
    # this function returns the html after the action
    def move_mouse_on(self, xpath: str):
        return self.observation(f"move_mouse_on(\"{xpath}\")")

    # Report agent's executed actions and observations.
    def report_action_history(self, error_msg=""):
        msg = f""
        for k, v in self.env.env_history.items():
            if int(k.split("obs_")[-1]) > self.last_report_step:
                msg += f"{k}: {v}\n"
        if error_msg:
            msg += error_msg
        self.last_report_step = self.env.action_step
        return msg

    # Report agent's current HTML.
    def report(self):
        msg = ""
        if self.last_html_string != self.cur_html_string:
            msg += "\nagent.cur_html_string:\n" + self.cur_html_string
            self.last_html_string = self.cur_html_string
        return msg
    
def click_and_type(agent, input_id, text):
    inputbox_xpath = f"//*[@id='{input_id}']"
    agent.click_xpath(inputbox_xpath)
    agent.type(text)
    
def turn_to_next_page(agent):
  next_page_xpath = f"//*[@id='pagination']/li[@class='page-item next']"
  html_string = agent.click_xpath(next_page_xpath)
  return html_string

MAX_ACTION_STEP = 20
class InteractEnv:
    # The InteractEnv class wraps the raw environment: 
    # It is responsible for converting actions to actions executable in the raw environment and capturing
    # post-execution observations and errors (including action conversion errors, action object errors, 
    # environment execution errors, etc.) or action success results, providing this information to the Agent. 
    # Then it detects whether the environment terminates (the raw environment terminated, maximum number of action 
    # steps reached, LLM actively terminated) and calculate the reward.
    # It will also record interactions between Agent and the environment, which can be used for reporting to LLM.
    
    def __init__(self, raw_env, env_id, env_name, epoch_id, obs, memory=None):
        self._env = raw_env
        self.env_id = env_id
        self.epoch_id = epoch_id
        self.task_type = env_name
        self.env_name = env_name
        self.init_info = f"\nHere is the task: {obs[0].utterance}\n The current web html is:\n{process_ob_html(obs)}\n"
        self.init_obs = process_ob_html(obs)
        self.task = obs[0].utterance
        self.env_history = {"obs_0": self.init_info}
        self.action_step = 0
        self.cur_obs = self.init_obs
        self.done = False
        self.reward = False
    
    def step(self, action):
        try:
            script = script_transform(action)
        except ValueError as e:
            return f'exception: {e}'
        observation, reward, done, info = self._env.step([script])
        obs = process_ob_html(observation)
        if obs is not None:
            self.cur_obs = obs
        self.reward, self.done = (reward[0]>0), all(done)
        
        self.action_step += 1
        obs_id = f"obs_{self.action_step}"
        self.env_history[obs_id] = f"Act: agent.{action}. Obs: {info['run_info']}"
        if self.action_step >= MAX_ACTION_STEP:
            self.done = True
            self.env_history[obs_id] += f" The agent has performed too many actions, exceeding the number of steps allowed to complete the task: {MAX_ACTION_STEP} steps."
        if self.done:
            feedback = f"Success: {self.reward}"
            # Since "tic-tac-toe" doesn't display the opponent's three-in-a-row, additional feedback is provided to remind the agent of the reason for its failure.
            if not self.reward and self.task_type=="tic-tac-toe":
                feedback += " You failed to prevent your opponent from forming a line."
            self.env_history[obs_id] += f" This epoch is done. {feedback}"
        return info['run_info']

def process_ob_html(obs):
    # If the step does not change the html, there is no html in the observation
    if not obs[0]:
        return None
    html_body = obs[0].html_body
    if obs[0].html_extra != '':
        html_body += obs[0].html_extra 
    return html_body

def script_transform(action):
    action = action.replace("\"", "")
    matches = re.search(r"\((.*)\)", action)
    para = matches.group(1)
    if action.startswith("type"):
        script = MiniWoBType(para)
    elif action.startswith("press_key"):
        key = para
        if key == 'enter':
            miniwob_key = '\n'
        elif key == 'space':
            miniwob_key = ' '
        elif key == 'arrow_left':
            miniwob_key = Keys.LEFT
        elif key == 'arrow_right':
            miniwob_key = Keys.RIGHT
        elif key == 'arrow_up':
            miniwob_key = Keys.UP
        elif key == 'arrow_down':
            miniwob_key = Keys.DOWN
        elif key == 'backspace':
            miniwob_key = Keys.BACKSPACE
        else:
            raise ValueError("Unknowned key pressed.")
        script = MiniWoBType(miniwob_key, press_key=True)
    elif action.startswith("click_option"):
        script = MiniWoBElementClickOption(para)
    elif action.startswith("click_xpath"):
        script = MiniWoBElementClickXpath(para)
    elif action.startswith("move_mouse_on"):
        script = MiniWoBMoveXpath(para)
    else:
        raise ValueError(f"unsupported action: {action}")
    return script