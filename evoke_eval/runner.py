"""Manage local vLLM services and ALFWorld evaluation workers."""
import argparse
import asyncio
import json
import os
import queue
import select
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from .metrics import medians, score
from .protocol import MAX_MODEL_LEN, MAX_STEPS, SEEDS, SPLITS, TASKS, encode, prompt_digest, request_payload

ROOT = Path(__file__).resolve().parents[1]


def runtime_environment():
    env = os.environ.copy()
    for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        env.setdefault(name, '2')
    env.setdefault('TOKENIZERS_PARALLELISM', 'false')
    return env


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.partial')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def load_cases(data_root, limit=None):
    cases = []
    for split, count in SPLITS.items():
        records = [json.loads(line) for line in (ROOT / 'manifests' / f'{split}.jsonl').read_text().splitlines()]
        if len(records) != count or len({r['game_id'] for r in records}) != count:
            raise ValueError(f'Invalid {split} manifest')
        for index, record in enumerate(records[:limit]):
            relative = Path(record['relative_gamefile'])
            game = (Path(data_root) / relative).resolve()
            if relative.is_absolute() or not game.is_relative_to(Path(data_root).resolve()):
                raise ValueError('Manifest paths must be relative to the data root')
            if not game.is_file():
                raise FileNotFoundError(game)
            if record['task_type'] not in TASKS:
                raise ValueError('Unknown task type in manifest')
            cases.append(dict(record, split=split, index=index, gamefile=str(game)))
    cases.sort(key=lambda case: (case['index'], case['split']))
    return cases


class Worker:
    def __init__(self, python, log):
        self.log = Path(log).open('x')
        self.proc = subprocess.Popen([str(python), str(ROOT / 'evoke_eval/environment.py')],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
                                     text=True, bufsize=1, env=runtime_environment())

    def request(self, payload):
        if self.proc.poll() is not None:
            raise RuntimeError(f'ALFWorld worker exited with {self.proc.returncode}')
        self.proc.stdin.write(json.dumps(payload, sort_keys=True) + '\n')
        self.proc.stdin.flush()
        if not select.select([self.proc.stdout], [], [], 120)[0]:
            raise TimeoutError('ALFWorld worker timed out')
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError('ALFWorld worker closed its output')
        response = json.loads(line)
        if response.get('ok') is not True:
            raise RuntimeError(f"{response.get('error_type')}: {response.get('error')}")
        return response

    def close(self):
        try:
            if self.proc.poll() is None:
                try:
                    self.request({'op': 'close'})
                    self.proc.wait(timeout=5)
                except Exception:
                    self.proc.terminate()
                    try:
                        self.proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.proc.kill()
                        self.proc.wait()
        finally:
            self.proc.stdin.close()
            self.proc.stdout.close()
            self.log.close()


def validate_state(state, steps):
    if state['steps'] != steps or len(state['history']) != 1 + 2 * steps:
        raise ValueError('Incomplete interaction history')
    if any('your task is to:' in item['text'].lower() for item in state['history']):
        raise ValueError('Goal text leaked into interaction history')
    if state['legal_actions'] != sorted(set(state['legal_actions'])):
        raise ValueError('The legal action list must be sorted and unique')
    if state['won'] and not state['done']:
        raise ValueError('A successful episode must be terminal')
    return state


async def evaluate_run(*, model, tokenizer, endpoint, cases, seed, output, alfworld_python):
    import httpx
    output = Path(output)
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite {output}')
    (output / 'workers').mkdir(parents=True)
    atomic_json(output / 'config.json', dict(model=model, temperature=0.0, seed=seed,
                max_steps=MAX_STEPS, max_model_len=MAX_MODEL_LEN,
                max_tokens_policy='longest legal completion including EOS',
                action_processing='strip outer whitespace only',
                games=[{k: c[k] for k in ('split', 'index', 'game_id', 'relative_gamefile')} for c in cases]))
    pending = asyncio.Queue()
    for case in cases:
        pending.put_nowait(case)
    rows = []
    async with httpx.AsyncClient(base_url=endpoint, timeout=240, trust_env=False,
                                limits=httpx.Limits(max_connections=32, max_keepalive_connections=0)) as client:
        async def lane(number):
            worker = None
            count = 0
            try:
                while not pending.empty():
                    case = pending.get_nowait()
                    if count % 8 == 0:
                        if worker is not None:
                            await asyncio.to_thread(worker.close)
                        worker = Worker(alfworld_python, output / 'workers' / f'{number:02d}-{count // 8:03d}.log')
                    response = await asyncio.to_thread(worker.request, dict(op='reset', gamefile=case['gamefile']))
                    state = validate_state(response['state'], 0)
                    goal, initial = state['goal'], state['history'][0]['text']
                    trajectory = []
                    while not state['done'] and len(trajectory) < MAX_STEPS:
                        prompt, budget = encode(tokenizer, state)
                        payload = request_payload(model, prompt, budget, seed)
                        for attempt in range(4):
                            try:
                                response = await client.post('/v1/completions', json=payload)
                                response.raise_for_status()
                                break
                            except (httpx.NetworkError, httpx.RemoteProtocolError, httpx.TimeoutException):
                                if attempt == 3:
                                    raise
                                await asyncio.sleep(0.5 * (2 ** attempt))
                        answer = response.json()
                        if answer['model'] != model or answer['usage']['prompt_tokens'] != len(prompt):
                            raise ValueError('The inference response does not match the requested model or prompt')
                        if len(answer['choices']) != 1:
                            raise ValueError('Expected exactly one completion')
                        choice = answer['choices'][0]
                        raw = choice['text']
                        action = raw.strip()
                        legal = state['legal_actions']
                        response = await asyncio.to_thread(worker.request, dict(op='step', action=action))
                        state = validate_state(response['state'], len(trajectory) + 1)
                        if state['goal'] != goal:
                            raise ValueError('The episode goal changed')
                        trajectory.append(dict(step=len(trajectory) + 1, raw_output=raw, action=action,
                            in_admissible_list=action in legal, legal_actions=legal,
                            post_observation=state['history'][-1]['text'], reward=state['reward'],
                            done=state['done'], won=state['won'], finish_reason=choice['finish_reason'],
                            completion_tokens=answer['usage']['completion_tokens'], max_new_tokens=budget,
                            prompt_tokens=len(prompt), prompt_token_sha256=prompt_digest(prompt), request_seed=seed))
                    row = dict(split=case['split'], index=case['index'], game_id=case['game_id'],
                               task_type=case['task_type'], seed=seed, temperature=0.0, success=state['won'],
                               steps=len(trajectory), initial_observation=initial, goal=goal, trajectory=trajectory,
                               termination='success' if state['won'] else 'environment_done' if state['done'] else 'step_cap')
                    atomic_json(output / 'episodes' / f"{case['split']}-{case['index']:04d}.json", row)
                    rows.append(row)
                    count += 1
                    print(f"seed={seed} {len(rows)}/{len(cases)} {case['split']} {case['index']} success={state['won']}", flush=True)
            finally:
                if worker is not None:
                    await asyncio.to_thread(worker.close)

        tasks = [asyncio.create_task(lane(index)) for index in range(min(32, len(cases)))]
        try:
            await asyncio.gather(*tasks)
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
    result = score(rows, cases)
    atomic_json(output / 'summary.json', result)
    return result


def service_command(model, port):
    return [sys.executable, '-m', 'vllm.entrypoints.openai.api_server', '--model', model,
            '--served-model-name', 'evoke', '--host', '127.0.0.1', '--port', str(port),
            '--dtype', 'bfloat16', '--seed', '20260816', '--generation-config', 'vllm',
            '--max-model-len', str(MAX_MODEL_LEN), '--max-num-seqs', '32',
            '--max-num-batched-tokens', '8192', '--gpu-memory-utilization', '0.80',
            '--enable-prefix-caching', '--enable-chunked-prefill']


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def wait_ready(proc, endpoint, timeout=900):
    import httpx
    deadline = time.monotonic() + timeout
    with httpx.Client(timeout=5, trust_env=False) as client:
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError('vLLM exited before becoming ready; see the service log')
            try:
                health = client.get(endpoint + '/health')
                if health.status_code == 200:
                    names = {m['id'] for m in client.get(endpoint + '/v1/models').json()['data']}
                    if 'evoke' not in names:
                        raise ValueError('vLLM did not register the expected model')
                    return
            except httpx.HTTPError:
                pass
            time.sleep(2)
    raise TimeoutError('vLLM did not become ready within 900 seconds')


def stop_service(proc):
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()


def main():
    parser = argparse.ArgumentParser(description='Evaluate an EVOKE full model on ALFWorld (T=0).')
    parser.add_argument('--model', required=True, help='Hugging Face model ID or local model directory')
    parser.add_argument('--data-root', type=Path, required=True, help='Directory containing valid_seen and valid_unseen')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--gpus', default=os.environ.get('CUDA_VISIBLE_DEVICES', '0'))
    parser.add_argument('--seeds', type=int, nargs='+', default=SEEDS)
    parser.add_argument('--num-episodes', type=int, help='Number of games per split for a quick check (at least 6)')
    parser.add_argument('--alfworld-python', type=Path,
                        default=Path(os.environ.get('ALFWORLD_PYTHON', ROOT / '.venv/alfworld/bin/python')))
    args = parser.parse_args()
    if args.num_episodes is not None and not 6 <= args.num_episodes <= min(SPLITS.values()):
        parser.error('--num-episodes must be between 6 and 134')
    if len(args.seeds) != len(set(args.seeds)):
        parser.error('--seeds must be unique')
    if not args.alfworld_python.is_file():
        parser.error('ALFWorld Python not found; run scripts/setup.sh or set --alfworld-python')
    gpus = args.gpus.split(',')
    if any(not gpu.strip() for gpu in gpus) or len(gpus) != len(set(gpus)):
        parser.error('--gpus must contain distinct GPU IDs')
    if args.output.exists():
        parser.error(f'Refusing to overwrite {args.output}')
    cases = load_cases(args.data_root, args.num_episodes)
    os.environ.update(runtime_environment())
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    args.output.mkdir(parents=True)
    atomic_json(args.output / 'status.json', {'state': 'running'})
    services, logs = [], []
    todo, errors, results = queue.Queue(), [], {}
    for seed in args.seeds:
        todo.put(seed)
    try:
        for gpu in gpus[:len(args.seeds)]:
            port = free_port()
            endpoint = f'http://127.0.0.1:{port}'
            log = (args.output / f'vllm-gpu{gpu}.log').open('x')
            logs.append(log)
            proc = subprocess.Popen(service_command(args.model, port),
                                    env={**runtime_environment(), 'CUDA_VISIBLE_DEVICES': gpu}, stdout=log,
                                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
            services.append((endpoint, proc))
        for endpoint, proc in services:
            wait_ready(proc, endpoint)

        def lane(endpoint):
            while not errors:
                try:
                    seed = todo.get_nowait()
                except queue.Empty:
                    return
                try:
                    results[seed] = asyncio.run(evaluate_run(model='evoke', tokenizer=tokenizer,
                        endpoint=endpoint, cases=cases, seed=seed, output=args.output / f't0_seed{seed}',
                        alfworld_python=args.alfworld_python))
                except BaseException as error:
                    errors.append(error)
                    return

        threads = [threading.Thread(target=lane, args=(endpoint,)) for endpoint, _ in services]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        if errors:
            raise RuntimeError(f'Evaluation failed: {errors[0]}') from errors[0]
        if set(results) != set(args.seeds):
            raise RuntimeError('Not all requested seeds completed')
        summary = dict(model=args.model, temperature=0.0, seeds=args.seeds,
                       full_evaluation=args.num_episodes is None,
                       runs={str(seed): results[seed] for seed in args.seeds},
                       median=medians(list(results.values())))
        atomic_json(args.output / 'summary.json', summary)
        atomic_json(args.output / 'status.json', {'state': 'done'})
        print(json.dumps(summary['median'], indent=2))
    except BaseException as error:
        atomic_json(args.output / 'status.json', {'state': 'failed', 'error': str(error)})
        raise
    finally:
        for _, proc in services:
            stop_service(proc)
        for log in logs:
            log.close()
