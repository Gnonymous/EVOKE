<h1 align="center">
EVOKE: Eliciting World Knowledge in Agents for Transferable Decision-Making
</h1>

<p align="center">
  <a href="#news">
    <img src="https://img.shields.io/badge/arXiv-Coming%20Soon-B31B1B?style=for-the-badge&logo=arxiv&logoColor=white" alt="arXiv Paper">
  </a>
  <a href="#release-plan">
    <img src="https://img.shields.io/badge/Code-Coming%20Soon-24292F?style=for-the-badge&logo=github&logoColor=white" alt="Code">
  </a>
  <a href="#release-plan">
    <img src="https://img.shields.io/badge/Model-Coming%20Soon-F59E0B?style=for-the-badge&logo=huggingface&logoColor=white" alt="Model Checkpoint">
  </a>
</p>

## News

- **2026-09**: Repository created. Paper, code, checkpoints, and data are coming soon.

If you have any questions ❓ or are interested in collaboration 🤝, please feel free to open an [issue](../../issues).

## Overview

**EVOKE** is a post-training method that elicits the world knowledge already inside pretrained LLM agents, so that they decide by the **consequences of their actions** rather than by contextual habits, and transfer to unseen environments.

LLM agents post-trained on a set of tasks often do well where they were trained, yet drop considerably in environments they have not seen. World-model methods address this by learning to **predict** future observations, at the cost of an extra prediction objective and errors that compound during planning. For agents acting in digital environments, however, much of this knowledge is already internalized during pretraining; the problem shifts from **acquiring** it to **eliciting** it. Typical post-training supervises each visited state under a single goal, so a policy can fit the labels by associating familiar contexts with habitual next actions.

EVOKE supplies the missing pressure through **goal diversity at fixed states**. It holds the environment state and interaction history fixed, swaps in alternative goals, and ranks the **same candidate actions** under each goal. Whenever the preferred action flips with the goal, no mapping from the context alone can rank the candidates correctly, which pushes the policy to draw on its knowledge of what each action does.

<div align="center">
  <img src="assets/overview.png" alt="EVOKE overview" style="width:85%;">
  <br>
  <em>Figure 1: From prediction to preference. (a) World-model approaches predict action consequences before choosing an action. (b) Under single-goal supervision, a policy can fit habits that fail to transfer. (c) EVOKE instead supervises action preferences at a fixed state and history under different goals.</em>
</div>

<br>

EVOKE repeats four stages:

1. **Policy rollout.** The current policy interacts with the environment to collect states and interaction histories.
2. **Goal intervention.** At each collected state, the original goal is kept and alternative goals achievable from the same state are added. The state, history, and available actions stay identical across goals.
3. **Action re-evaluation.** Candidate actions are executed from the same state, and each is labeled under every goal as advancing it or not, grounded in the observed outcome.
4. **Iterative preference learning.** The policy is trained by contrastive ranking against its own favored mistakes, and each round aggregates the data of all previous rounds.

At inference time, EVOKE is a standard policy. It requires no world-model module, no inference-time planning, and no annotator at deployment.

<div align="center">
  <img src="assets/pipeline.png" alt="EVOKE training loop" style="width:100%;">
  <br>
  <em>Figure 2: The EVOKE training loop. Actions can switch between positive and competing across goals.</em>
</div>

## Main Results

Across ALFWorld, WebShop, and search-based QA with three backbones (Qwen2.5-3B/7B-Instruct and Qwen3-1.7B), the experiments show four main findings:

1. **EVOKE performs best across benchmarks and backbones.** It achieves the best average on every benchmark and backbone, including all world-model and dynamics methods on 7B, with the largest margins on the multi-step ALFWorld and WebShop tasks.
2. **EVOKE transfers to unseen environments.** On unseen ALFWorld games, it reaches **91.1% / 93.1% / 84.6%** average success with Qwen2.5-3B / Qwen2.5-7B / Qwen3-1.7B, the best on each backbone.
3. **The gains come from goal interventions and ranking.** Removing alternative goals drops unseen success from **91.8%** to **82.8%**, and training longer on the original goals does not close the gap. Imitating the same goal data instead of ranking it falls **7.5** points behind on unseen games.
4. **The knowledge is already there; EVOKE makes the policy use it.** Action consequences are linearly decodable from the original backbone before any task training. EVOKE makes the policy decide by the goal rather than by habit, with the fewest habitual errors (**6.4%** of decisions), and solves **91.0%** of unseen games within 20 actions.

<div align="center">
  <img src="assets/main_results.png" alt="EVOKE main results" style="width:100%;">
  <br>
  <em>Figure 3: Main results on ALFWorld and WebShop (left) and search-based QA (right).</em>
</div>

<br>

<div align="center">
  <img src="assets/unseen_results.png" alt="EVOKE unseen ALFWorld results" style="width:85%;">
  <br>
  <em>Figure 4: Generalization to unseen ALFWorld games.</em>
</div>

## Release Plan

- [ ] Paper on arXiv
- [ ] Training and evaluation code (ALFWorld, WebShop, search-based QA)
- [ ] Trained checkpoints (LoRA adapters)
- [ ] Goal-intervention preference data
- [ ] Scripts to reproduce the main results and analyses

## Citation

The BibTeX entry will be added once the paper is available on arXiv.
