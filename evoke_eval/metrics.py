"""Validate complete runs and summarize task and overall success."""
import statistics
from .protocol import SPLITS, TASKS


def score(rows, cases):
    expected = {(case['split'], case['index']) for case in cases}
    actual = [(row['split'], row['index']) for row in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError('The evaluation contains missing, duplicate, or unexpected episodes')
    result = {}
    for split in SPLITS:
        eps = [row for row in rows if row['split'] == split]
        tasks = {}
        for task in TASKS:
            group = [row for row in eps if row['task_type'] == task]
            if not group:
                raise ValueError(f'No episodes for {split}/{task}')
            tasks[task] = 100 * sum(row['success'] for row in group) / len(group)
        successes = sum(row['success'] for row in eps)
        result[split] = dict(tasks=tasks, macro=statistics.mean(tasks.values()),
                             overall=100 * successes / len(eps), successes=successes, episodes=len(eps))
    return result


def medians(runs):
    return {split: dict(macro=statistics.median(run[split]['macro'] for run in runs),
                        overall=statistics.median(run[split]['overall'] for run in runs),
                        tasks={task: statistics.median(run[split]['tasks'][task] for run in runs)
                               for task in TASKS}) for split in SPLITS}
