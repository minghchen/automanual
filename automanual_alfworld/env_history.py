import re

class Agent:
    # The Agent class is responsible for processing the pythonic actions output by the LLM, 
    # passing them to the InteractEnv. It gets the result of the action from the environment 
    # (success or failure information), the new observation and whether it is completed or not. 
    # It is also responsible for reporting the results of these executions to the LLM.

    def __init__(self, env):
        self.env = env
        self.location = "middle of room"
        self.holding = "nothing"
        self.is_success = False
        self.last_report_step = 0

    # Get an observation from the environment after performing an action
    def observation(self, action):
        if self.env.done:
            return "Done."
        observation = self.env.step(action)
        self.location = self.env.cur_loc 
        self.holding = self.env.holding
        return observation

    def go_to(self, receptacle):
        return self.observation(f"go_to('{receptacle}')")
    
    def open(self, receptacle):
        return self.observation(f"open('{receptacle}')")
    
    def close(self, receptacle):
        return self.observation(f"close('{receptacle}')")
    
    def use(self, object):
        return self.observation(f"use('{object}')")

    def take_from(self, object, receptacle):
        return self.observation(f"take_from('{object}', '{receptacle}')")
        
    def put_in_or_on(self, object, receptacle):
        return self.observation(f"put_in_or_on('{object}', '{receptacle}')")    

    def clean_with(self, object, receptacle):
        return self.observation(f"clean_with('{object}', '{receptacle}')")

    def heat_with(self, object, receptacle):
        return self.observation(f"heat_with('{object}', '{receptacle}')")

    def cool_with(self, object, receptacle):
        return self.observation(f"cool_with('{object}', '{receptacle}')")
    
    # Report agent's current state, including its location, what it's holding, and last few actions and observations.
    def report(self, error_msg=""):
        msg = f""
        for k, v in self.env.env_history.items():
            if int(k.split("obs_")[-1]) > self.last_report_step:
                msg += f"{k}: {v}\n"
        if error_msg:
            msg += error_msg
        msg += f"Current state: You are at {self.location} and holding {self.holding}."
        self.last_report_step = self.env.action_step
        return msg

# Extracts a list of object_ids with the specified object_name from the observation.
def get_object_with_id(observation, object_name):
    pattern = fr"\b{object_name}_\d+"
    object_ids = re.findall(pattern, observation)
    return object_ids

# Define a helper method to find object that is needed
def find_object(agent, recep_to_check, object_name):
    for receptacle in recep_to_check:
        observation = agent.go_to(receptacle)
        # Check if we need to open the receptacle. If we do, open it.
        if 'closed' in observation:
            observation = agent.open(receptacle)
        # Check if the object is in/on the receptacle.
        if object_name in observation:
            object_ids = get_object_with_id(observation, object_name)
            return object_ids, receptacle
    return None, None

# Define a helper method to put object in/on the target receptacle
def go_to_put_object(agent, target_receptacle, object_id):
    observation = agent.go_to(target_receptacle)
    # check if target_receptacle is closed. If so, open it.
    if 'closed' in observation:
        observation = agent.open(target_receptacle)
    observation = agent.put_in_or_on(object_id, target_receptacle)
    return observation

MAX_ACTION_STEP = 50
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
        self.task_type = env_name.split("-")[0]
        self.init_info = f"\nHere is the task:\n{obs}"
        self.init_obs = obs.split('\n')[0]
        self.task = obs.split('\n')[1].replace("Your task is to: ", "")
        self.env_history = {"obs_0": self.init_info}
        self.action_step = 0
        self.last_obs = ""
        self.cur_loc = ""
        self.holding = "nothing"
        self.done = False
        self.reward = False

    def step(self, action):
        try:
            script = script_transform(action)
        except ValueError as e:
            return f'exception: {e}'
        observation, _, done, info = self._env.step([script])
        observation, self.reward, self.done = observation[0], info['won'][0], done[0]
        
        self.action_step += 1
        observation = process_ob(observation)
        if "Nothing happens" not in observation:
            self.last_obs = observation
            if "go to" in script:
                self.cur_loc = re.search(r'go to (\S+)', script).group(1)
                self.cur_loc_info = observation
            if "open" in script or "close" in script:
                self.cur_loc_info = observation
            if "take" in script:
                self.holding = re.search(r"(?<=take\s)(.*?)(?=\sfrom)", script).group(1)
                self.cur_loc_info = ""
            if "put" in script:
                self.holding = "nothing"
                self.cur_loc_info = ""
        elif "go to" in script:
            loc = re.search(r'go to (\S+)', script).group(1)
            if loc == self.cur_loc: 
                observation = self.cur_loc_info
        observation += f" You are at {self.cur_loc} and holding {self.holding}." # agent.location: {self.cur_loc}, agent.holding: {self.holding}.
        obs_id = f"obs_{self.action_step}"
        self.env_history[obs_id] = f"Act: agent.{action}. Obs: {observation}"
        if self.action_step >= MAX_ACTION_STEP:
            self.done = True
            self.env_history[obs_id] += f" The agent has performed too many actions, exceeding the number of steps allowed to complete the task: {MAX_ACTION_STEP} steps. This epoch is done. Succeed: {self.reward}"
        elif self.done:
            self.env_history[obs_id] += f" This epoch is done. Succeed: {self.reward}"
        return observation
    
def process_ob(obs):
    if obs.startswith('You arrive at loc'):
        obs = obs[obs.find('. ')+2:]    
    return obs
    
def script_transform(action):
    action = action.replace("'", "")
    if "go_to" in action:
        script = re.sub(r'go_to\((.*?)\)', r'go to \1', action)
    elif "open" in action:
        script = re.sub(r'open\((.*?)\)', r'open \1', action)
    elif "close" in action:
        script = re.sub(r'close\((.*?)\)', r'close \1', action)
    elif "take_from" in action:
        script = re.sub(r'take_from\((.*?), (.*?)\)', r'take \1 from \2', action)
    elif "put_in_or_on" in action:
        script = re.sub(r'put_in_or_on\((.*?), (.*?)\)', r'put \1 in/on \2', action)
    elif "heat_with" in action:
        script = re.sub(r'heat_with\((.*?), (.*?)\)', r'heat \1 with \2', action)
    elif "cool_with" in action:
        script = re.sub(r'cool_with\((.*?), (.*?)\)', r'cool \1 with \2', action)
    elif "clean_with" in action:
        script = re.sub(r'clean_with\((.*?), (.*?)\)', r'clean \1 with \2', action)
    elif "inventory" in action:
        script = re.sub(r'inventory\((.*?)\)', r'inventory', action)
    elif "look" in action:
        script = re.sub(r'look\((.*?)\)', r'look', action)
    elif "use" in action:
        script = re.sub(r'use\((.*?)\)', r'use \1', action)
    elif "examine" in action:
        script = re.sub(r'examine\((.*?)\)', r'examine \1', action)
    else:
        raise ValueError(f"unsupported action: {action}")
    return script
        