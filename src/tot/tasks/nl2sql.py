import os
import re
import json
from tot.tasks.base import Task, DATA_PATH
from tot.prompts.text import *
from tot.models import gpt


class NL2SQLTask(Task):
    """
    Input (x)   : a text instruction
    Output (y)  : a text generation
    Reward (r)  : # TODO
    Input Example: 
    Output Example: 
    """
    def __init__(self, file='spider_dev.json'):
        """
        file: a text file, each line is some sentences
        """
        super().__init__()
        path = os.path.join(DATA_PATH, 'nl2sql', file)
        self.data = json.load(open(path))
        self.steps = 10 # max_step
        self.stops = ['\nQ :'] * self.steps

    def __len__(self) -> int:
        return len(self.data)
    
    def get_input(self, idx: int) -> str:
        return self.data[idx]["input"], self.data[idx]["question"]
    
    @staticmethod
    def standard_prompt_wrap(x: str, y:str='') -> str:
        raise NotImplementedError

    @staticmethod
    def cot_prompt_wrap(x: str, y:str='') -> str:
        """ 
        y must be the concat of all previous steps.
        """
        return cot_prompt.format(input=x) + y

    @staticmethod
    def is_finished(question: str, y: str) -> bool:
        last_generated_question = ''
        for line in y.split('\n')[::-1]: # check from the last line
            line = line.strip()
            if line.startswith('Q :'):
                last_generated_question = line[3:].strip()
                break 
            
        if last_generated_question.lower() == question.lower():
            return True 
        return False 
    
    @staticmethod
    def vote_prompt_wrap(x: str, ys: list) -> str:
        prompt = vote_prompt
        for i, y in enumerate(ys, 1):
            # y = y.replace('Plan:\n', '')
            # TODO: truncate the plan part?
            prompt += f'Choice {i}:\n{y}\n'
        return prompt
    
    @staticmethod
    def vote_outputs_unwrap(vote_outputs: list, n_candidates: int) -> list:
        vote_results = [0] * n_candidates
        for vote_output in vote_outputs:
            pattern = r".*best choice is .*(\d+).*"
            match = re.match(pattern, vote_output, re.DOTALL)
            if match:
                vote = int(match.groups()[0]) - 1
                if vote in range(n_candidates):
                    vote_results[vote] += 1
            else:
                print(f'vote no match: {[vote_output]}')
        return vote_results
