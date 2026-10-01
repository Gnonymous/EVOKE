"""Prompt and decoding settings shared by the released models."""
import hashlib
import json
from collections.abc import Mapping

SYSTEM_PROMPT = (
    "You are an ALFWorld agent. Choose exactly one action from the provided "
    "legal-action list. Return only that action, with no explanation."
)
MAX_STEPS = 50
MAX_MODEL_LEN = 32768
TASKS = ["pick_and_place_simple", "look_at_obj_in_light", "pick_clean_then_place_in_recep",
         "pick_heat_then_place_in_recep", "pick_cool_then_place_in_recep", "pick_two_obj_and_place"]
SPLITS = {"valid_seen": 140, "valid_unseen": 134}
SEEDS = [20260911, 20260912, 20260913]


def messages(state):
    history = [f"{item['role'].capitalize()}: {item['text']}" for item in state['history']]
    actions = [f"- {action}" for action in state['legal_actions']]
    text = '\n'.join(("Goal:", state['goal'], "", "Interaction history:", *history,
                      "", "Legal actions (choose exactly one):", *actions))
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}]


def token_list(value):
    if isinstance(value, Mapping):
        value = value['input_ids']
    if hasattr(value, 'tolist'):
        value = value.tolist()
    if not isinstance(value, list) or any(not isinstance(token, int) for token in value):
        raise TypeError('The chat template must return a flat token list')
    return value


def encode(tokenizer, state):
    chat = messages(state)
    prompt = token_list(tokenizer.apply_chat_template(chat, tokenize=True, add_generation_prompt=True))
    eos = tokenizer.eos_token_id
    eos_ids = {eos} if isinstance(eos, int) else set(eos or [])
    budgets = []
    for action in state['legal_actions']:
        full = token_list(tokenizer.apply_chat_template(
            chat + [{"role": "assistant", "content": action}],
            tokenize=True, add_generation_prompt=False))
        if full[:len(prompt)] != prompt:
            raise ValueError('The completion does not preserve the prompt prefix')
        completion = full[len(prompt):]
        for index, token in enumerate(completion):
            if token in eos_ids:
                completion = completion[:index + 1]
                break
        if not completion:
            raise ValueError('A legal action has an empty completion')
        budgets.append(len(completion))
    if not budgets:
        raise ValueError('No legal actions are available')
    budget = max(budgets)
    if len(prompt) + budget > MAX_MODEL_LEN:
        raise ValueError('Full history exceeds the model context length')
    return prompt, budget


def request_payload(model, prompt, budget, seed):
    return dict(model=model, prompt=prompt, temperature=0.0, max_tokens=budget,
                seed=seed, top_p=1.0, top_k=-1, min_p=0.0, repetition_penalty=1.0)


def prompt_digest(prompt):
    return hashlib.sha256(json.dumps(prompt).encode()).hexdigest()
