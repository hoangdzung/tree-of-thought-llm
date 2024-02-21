import itertools
import numpy as np
from functools import partial
from tot.models import gpt
from tot import tasks

def get_value(task, x, y, n_evaluate_sample, cache_value=True):
    value_prompt = task.value_prompt_wrap(x, y)
    if cache_value and value_prompt in task.value_cache:
        return task.value_cache[value_prompt]
    value_outputs = gpt(value_prompt, n=n_evaluate_sample, stop=None)
    value = task.value_outputs_unwrap(x, y, value_outputs)
    if cache_value:
        task.value_cache[value_prompt] = value
    return value

def get_values(task, x, ys, n_evaluate_sample, cache_value=True):
    values = []
    local_value_cache = {}
    for y in ys:  # each partial output
        if y in local_value_cache:  # avoid duplicate candidates
            value = 0
        else:    
            value = get_value(task, x, y, n_evaluate_sample, cache_value=cache_value)
            local_value_cache[y] = value
        values.append(value)
    return values

def get_votes(task, x, ys, n_evaluate_sample):
    vote_prompt = task.vote_prompt_wrap(x, ys)
    vote_outputs = gpt(vote_prompt, n=n_evaluate_sample, stop=None)
    values = task.vote_outputs_unwrap(vote_outputs, len(ys))
    return values

def get_proposals(task, x, y): 
    propose_prompt = task.propose_prompt_wrap(x, y)
    proposals = gpt(propose_prompt, n=1, stop=None)[0].split('\n')
    return [y + _ + '\n' for _ in proposals]

def get_samples(task, x, y, n_generate_sample, prompt_sample, stop):
    if prompt_sample == 'standard':
        prompt = task.standard_prompt_wrap(x, y)
    elif prompt_sample == 'cot':
        prompt = task.cot_prompt_wrap(x, y)
    else:
        raise ValueError(f'prompt_sample {prompt_sample} not recognized')
    samples = gpt(prompt, n=n_generate_sample, stop=stop)
    return [y + _ for _ in samples]

def solve(args, task, idx, to_print=True):
    global gpt
    is_nl2sql = isinstance(task, tasks.nl2sql.NL2SQLTask)
    if is_nl2sql:
        assert args.method_generate == 'sample' and args.method_evaluate == 'vote', \
            f"Only support `sample` generation and `vote` evaluation for NL2SQL, but got {args.method_generate} and {args.method_evaluate}"

    gpt = partial(gpt, model=args.backend, temperature=args.temperature)
    print(gpt)
    if is_nl2sql:
        x, question = task.get_input(idx) # schema + question, question
    else:
        x = task.get_input(idx)  # input
    ys = ['']  # current output candidates
    infos = []
    finished_ys = []
    for step in range(task.steps):
        # generation
        # if args.method_generate == 'sample':
        #     new_ys = [get_samples(task, x, y, args.n_generate_sample, prompt_sample=args.prompt_sample, stop=task.stops[step]) for y in ys]
        # elif args.method_generate == 'propose':
        #     new_ys = [get_proposals(task, x, y) for y in ys]
        
        new_ys = []
        for y in ys:
            if args.method_generate == 'sample':
                new_steps = get_samples(task, x, y, args.n_generate_sample, prompt_sample=args.prompt_sample, stop=task.stops[step])
            elif args.method_generate == 'propose':
                new_steps = get_proposals(task, x, y)
            
            if is_nl2sql: # we need to concate steps
                new_steps = [y + new_step for new_step in new_steps]
            new_ys.append(new_steps)
        new_ys = list(itertools.chain(*new_ys))
        ids = list(range(len(new_ys)))
        # evaluation
        if args.method_evaluate == 'vote':
            values = get_votes(task, x, new_ys, args.n_evaluate_sample)
        elif args.method_evaluate == 'value':
            values = get_values(task, x, new_ys, args.n_evaluate_sample)

        # selection
        if args.method_select == 'sample':
            ps = np.array(values) / sum(values)
            select_ids = np.random.choice(ids, size=args.n_select_sample, p=ps).tolist()
        elif args.method_select == 'greedy':
            select_ids = sorted(ids, key=lambda x: values[x], reverse=True)[:args.n_select_sample]
        select_new_ys = [new_ys[select_id] for select_id in select_ids]

        # log
        if to_print: 
            sorted_new_ys, sorted_values = zip(*sorted(zip(new_ys, values), key=lambda x: x[1], reverse=True))
            print(f'-- new_ys --: {sorted_new_ys}\n-- sol values --: {sorted_values}\n-- choices --: {select_new_ys}\n')
        
        infos.append({'step': step, 'x': x, 'ys': ys, 'new_ys': new_ys, 'values': values, 'select_new_ys': select_new_ys})

        if is_nl2sql: # for nl2sql task, we don't know the number of steps in advance
            ys = []
            for value, select_new_y in zip(values, select_new_ys):
                if task.is_finished(question, select_new_y):
                    finished_ys.append((select_new_y, value))
                    continue
                if not select_new_y.endswith('\n'):
                    select_new_y += '\n'
                ys.append(select_new_y)
        else: 
            ys = select_new_ys   
        if len(ys) == 0:
            break 
    if to_print: 
        if is_nl2sql:
            print(finished_ys)
        else:
            print(ys)

    if is_nl2sql:
        return finished_ys, {'steps': infos}
    return ys, {'steps': infos}

def naive_solve(args, task, idx, to_print=True):
    global gpt
    gpt = partial(gpt, model=args.backend, temperature=args.temperature)
    print(gpt)
    x = task.get_input(idx)  # input
    ys = get_samples(task, x, '', args.n_generate_sample, args.prompt_sample, stop=None)
    return ys, {}