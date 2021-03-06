"""
Classic cart-pole example implemented with an FMU simulating a cart-pole system.
Implementation inspired by OpenAI Gym examples:
https://github.com/openai/gym/blob/master/gym/envs/classic_control/cartpole.py
"""

import logging
import math
import numpy as np
from gym import spaces
from modelicagym.environment import DymolaBaseEnv

logger = logging.getLogger(__name__)

class IEEE9Env(DymolaBaseEnv):
    """
    Wrapper class for creation of cart-pole environment using JModelica-compiled FMU (FMI standard v.2.0).

    Attributes:
        m_cart (float): mass of a cart.

        m_pole (float): mass of a pole.

        theta_0 (float): angle of the pole, when experiment starts.
        It is counted from the positive direction of X-axis. Specified in radians.
        1/2*pi means pole standing straight on the cast.

        theta_dot_0 (float): angle speed of the poles mass center. I.e. how fast pole angle is changing.
        time_step (float): time difference between simulation steps.
        positive_reward (int): positive reward for RL agent.
        negative_reward (int): negative reward for RL agent.
    """

    def __init__(self, mo_name, libs, default_action, time_step, positive_reward,
                 negative_reward, log_level, method):

        logger.setLevel(log_level)

        self.viewer = None
        self.display = None

        self.action_names = ['G1.k','G2.k','G3.k']
        self.state_names = [
                            'integrator[1]',
                            'integrator[2]',
                            'integrator[3]',
                            'integrator[4]',
                            'integrator[5]',
                            'integrator[6]',
                            'integrator[7]',
                            'integrator[8]',
                            'integrator[9]',
                            'G1.gENSAL.P','G2.gENROU.P','G3.gENROU.P',
                            'load_B8.P', 'load_B6.P', 'load_B5.P',
                            'my_time',
                            'load_B5.rising']
        # for a time averaged version:
        # self.state_names = ['b1_average.y', 'b2_average.y', ...]
        config = {
            'model_input_names': self.action_names,
            'model_output_names': self.state_names,
            'model_parameters': {},
            'initial_state': (1),
            'time_step': time_step,
            'positive_reward': positive_reward,
            'negative_reward': negative_reward,
            'default_action': default_action,
            'method': method,
            'additional_debug_states': [f'B{i}.V' for i in range(1,10)]
        }

        self.n_steps = 0
        # self._normalize_reward()
        self.max_reward = 0.5
        self.min_reward = -0.5
        self.avg_reward = 0
        self.cached_values = None
        self.cached_state = None
        # change this to unpack the dictionary __init__(**config), so that some parameters can have default values
        super().__init__(mo_name, libs, config, log_level)



    # def postprocess_state(self, state):
    #     return state
    def postprocess_state(self, state):
        processed_states = []
        for s in state:
            if isinstance(s, list): # this is lazy and will only work when the whole list is of integrated values
                if self.cached_values:
                    processed_states += list(np.divide(np.subtract(s, self.cached_values),self.tau))
                    self.cached_values = s # this implementation only works when there is "one" variable that is integrated
                else:
                    processed_states += list(np.divide(s,self.tau))
                    self.cached_values = s
            else:
                processed_states += [s]
        return processed_states

    def _get_action_space(self):
        low = -1*np.ones(len(self.action_names))
        high = np.ones(len(self.action_names))
        return spaces.Box(low, high)

    def _get_observation_space(self):
        low = -1*np.ones(len(self.state_names))
        high = 1*np.ones(len(self.state_names))
        return spaces.Box(low, high)

    def _reward_policy(self):
        if self.cached_state:
            avg_voltages = np.subtract(self.state[:9], self.cached_state[:9])
        else:
            avg_voltages = np.array(self.state[:9])
        avg_voltages = avg_voltages / self.tau
        reward = -1*np.linalg.norm(100*avg_voltages)
        # normalized_reward = (reward - self.avg_reward) / (self.max_reward - self.min_reward)
        self.cached_state = self.state
        return reward

    # def get_state(self, results):
    #     res = super().get_state(results)
    #     res += []

    def step(self, action):
        self.n_steps += 1
        action = np.multiply(action, 0.2)
        return super().step(list(action))

    def render(self, mode='human', close=False):
        return

    def close(self):
        return self.render(close=True)
