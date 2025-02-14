# -*- coding: utf-8 -*-
"""game_hack.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1yJ3_2YxobI7mRdajI8a_A7drRotwbpC8

# Prisioners Dynamical System

This is a cadCAD implementation of a Generalized Dynamical Systems representation of the Repeated Prisioners Dilemma

Authors: Michael Zargham (zargham@block.science), Danilo Lessa Bernardineli (danilo@block.science) and Matt Stephenson (matt@block.science)
"""

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# # Install extra dependencies
# !pip install cadCAD-tools
# !pip install ipython-autotime
# !pip install holoviews
# !pip install hvplot
# !pip install hvnx
# 
# # Automatically print time
# %load_ext autotime

"""## Dependencies"""

# For running the cadCAD representation

from cadCAD.configuration.utils import config_sim
from cadCAD.configuration import Experiment

from cadCAD_tools.types import Param, ParamSweep
from cadCAD_tools.preparation import prepare_params

# For numerics & analytics
import numpy as np
import scipy.stats as st

"""## Model & simulation set-up"""

MONTE_CARLO_RUNS = 5
SIMULATION_TIMESTEPS = 500
N_AGENTS = 15
INITIAL_GOODWILL = 0.8


sys_params = {
    'coordinate_param': Param(10, float),
    'exploiter_param': Param(15, float),
    'exploited_param': Param(0, float),
    'defect_param': Param(2, float),
    'coordinate_goodwill': ParamSweep([1.2, 2.0], float),
    'exploiter_goodwill': ParamSweep([1.0], float),
    'exploited_goodwill': ParamSweep([0.4, 0.8], float),
    'defect_goodwill': ParamSweep([0.8, 1.2], float),
    'max_goodwill': Param(0.95, float),
    'min_goodwill': Param(0.05, float)
}

sys_params = prepare_params(sys_params, True)

genesis_states = {
    'goodwill': np.ones((N_AGENTS, N_AGENTS)) * INITIAL_GOODWILL,
    'decisions': np.ones((N_AGENTS, N_AGENTS)) * np.nan,
    'rewards': np.zeros(N_AGENTS)
    
}

@np.vectorize
def agent_choice(goodwill: float) -> float:
    return st.bernoulli.rvs(goodwill)

def get_payout(agent_index: int,
               counterparty_index: int,
               choices: list,
               params) -> float:        
        i = agent_index
        j = counterparty_index
        
        i_choice = choices[i][j]
        j_choice = choices[j][i]
        
        if (i_choice == 1.0) & (j_choice == 1.0):
            return params['coordinate_param']
        elif (i_choice == 1.0) & (j_choice == 0.0):
            return params['exploiter_param']
        elif (i_choice == 0.0) & (j_choice == 1.0):
            return params['exploited_param']
        elif (i_choice == 0.0) & (j_choice == 0.0):
            return params['defect_param']


def get_goodwill(agent_index: int,
               counterparty_index: int,
               choices: list,
               goodwill: float,
               params) -> float:        
        i = agent_index
        j = counterparty_index
        
        i_choice = choices[i][j]
        j_choice = choices[j][i]

        if (i_choice == 1.0) & (j_choice == 1.0):
            return np.clip(goodwill * params['coordinate_goodwill'], 
                           params['min_goodwill'], 
                           params['max_goodwill'])
        elif (i_choice == 1.0) & (j_choice == 0.0):
            return np.clip(goodwill * params['exploiter_goodwill'], 
                           params['min_goodwill'], 
                           params['max_goodwill'])
        elif (i_choice == 0.0) & (j_choice == 1.0):
            return np.clip(goodwill * params['exploited_goodwill'], 
                           params['min_goodwill'], 
                           params['max_goodwill'])
        elif (i_choice == 0.0) & (j_choice == 0.0):
            return np.clip(goodwill * params['defect_goodwill'], 
                           params['min_goodwill'], 
                           params['max_goodwill'])


def p_agent_choices(params, step, sL, s):
    choices = agent_choice(s['goodwill'])
    return {'choices': choices}


def s_goodwill(params, _2, _3, prev_state, policy_input):
    choices = policy_input['choices']  
    N_agents = len(prev_state['goodwill'])
    old_goodwill = prev_state['goodwill']
    new_goodwill = prev_state['goodwill'].copy()
    for i in range(N_agents):
      for j in range(N_agents):
        if i == j:
          continue
        else:
          new_goodwill[i] = get_goodwill(i, j, choices, old_goodwill[i][j], params)
    return ('goodwill', new_goodwill)

def s_choices(params, 
                substep, 
                state_history, 
                prev_state, 
                policy_input):
    value = policy_input['choices']
    return ('decisions', value)


def s_rewards(params, 
                substep, 
                state_history, 
                prev_state, 
                policy_input):
    choices = policy_input['choices']  
    N_agents = len(prev_state['rewards'])
    rewards = prev_state['rewards'].copy()
    for i in range(N_agents):
      for j in range(N_agents):
        if i == j:
          continue
        else:
          rewards[i] += get_payout(i, j, choices, params)
    return ('rewards', rewards)


partial_state_update_blocks = [
    {
        'policies': {
           'decision_making': p_agent_choices
        },
        'variables': {
            'decisions': s_choices,
            'rewards' : s_rewards,
            'goodwill': s_goodwill
        }
    }
]


sim_params = {
    'T': range(500),
    'N': 3,
    'M': sys_params
}
exp = Experiment()
c = config_sim(sim_params)

exp.append_model(model_id='base_simulation',
                 initial_state=genesis_states,
                 partial_state_update_blocks=partial_state_update_blocks,
                 sim_configs=c)

sim_params = {
    'T': range(1000),
    'N': 10,
    'M': sys_params
}
d = config_sim(sim_params)

exp.append_model(model_id='long_simulation',
                 initial_state=genesis_states,
                 partial_state_update_blocks=partial_state_update_blocks,
                 sim_configs=d)