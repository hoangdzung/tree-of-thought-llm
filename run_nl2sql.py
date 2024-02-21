import argparse
from tot.methods.bfs import solve
from tot.tasks.nl2sql import NL2SQLTask

args = argparse.Namespace(
            backend='gpt-3.5-turbo', 
            temperature=0.7, 
            task='nl2sql', 
            naive_run=False, 
            prompt_sample='cot', 
            method_generate='sample', 
            method_evaluate='vote', 
            method_select='greedy', 
            n_generate_sample=2, 
            n_evaluate_sample=2, 
            n_select_sample=2)

task = NL2SQLTask()
ys, infos = solve(args, task, 1033)
import pdb;pdb.set_trace()