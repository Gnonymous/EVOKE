"""TextWorld worker; runs in the ALFWorld Python environment."""
import contextlib
import json
import re
import sys
import traceback
from pathlib import Path

GOAL_PATTERN = re.compile(r'\n\nYour task is to:\s*(?P<goal>.*?)(?=\n\n|\Z)', re.IGNORECASE | re.DOTALL)


def strip_goal(text):
    return GOAL_PATTERN.sub('', text).rstrip()


class Session:
    def __init__(self, gamefile):
        import textworld
        from alfworld.agents.environment.alfred_tw_env import AlfredDemangler, AlfredInfos
        self.env = textworld.start(str(gamefile), textworld.EnvInfos(admissible_commands=True, won=True, facts=True),
                                   wrappers=[AlfredDemangler(shuffle=False), AlfredInfos])

    def reset(self):
        self.state = self.env.reset()
        feedback = str(self.state['feedback'])
        match = GOAL_PATTERN.search(feedback)
        if not match:
            raise ValueError('The episode has no explicit goal')
        self.goal = match.group('goal').strip()
        self.history = [{'role': 'observation', 'text': strip_goal(feedback)}]
        self.done = bool(self.state['won'])
        self.steps = 0
        self.reward = 0.0
        return self.payload()

    def step(self, action):
        if self.done:
            raise RuntimeError('The episode is already terminal')
        self.history.append({'role': 'action', 'text': action})
        self.state, self.reward, done = self.env.step(action)
        self.history.append({'role': 'observation', 'text': strip_goal(str(self.state['feedback']))})
        self.steps += 1
        self.done = bool(done or self.state['won'])
        return self.payload()

    def payload(self):
        return dict(goal=self.goal, history=list(self.history), legal_actions=sorted(self.state['admissible_commands']),
                    won=bool(self.state['won']), done=self.done, steps=self.steps, reward=float(self.reward))

    def close(self):
        self.env.close()


def main():
    session = None
    gamefile = None
    try:
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                req = json.loads(line)
                # The pipe carries JSON only; third-party diagnostics go to stderr.
                with contextlib.redirect_stdout(sys.stderr):
                    if req['op'] == 'close':
                        response = {'ok': True}
                    elif req['op'] == 'reset':
                        candidate = str(Path(req['gamefile']))
                        if candidate != gamefile:
                            if session is not None:
                                session.close()
                            session = Session(candidate)
                            gamefile = candidate
                        response = {'ok': True, 'state': session.reset()}
                    elif req['op'] == 'step' and session is not None:
                        response = {'ok': True, 'state': session.step(req['action'])}
                    else:
                        raise ValueError('Invalid worker operation')
                print(json.dumps(response, sort_keys=True), flush=True)
                if req['op'] == 'close':
                    break
            except Exception as error:
                print(json.dumps(dict(ok=False, error_type=type(error).__name__, error=str(error),
                                      traceback=traceback.format_exc())), flush=True)
    finally:
        if session is not None:
            session.close()


if __name__ == '__main__':
    main()
