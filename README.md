<div align="center">

# 🌱 EVOKE: Eliciting World Knowledge in Agents for Transferable Decision-Making

[![arXiv](https://img.shields.io/badge/arXiv-coming%20soon-b31b1b.svg?logo=arxiv&logoColor=white)](#-updates)
[![Code](https://img.shields.io/badge/Code-coming%20soon-lightgrey.svg?logo=github)](#-release-plan)
[![Checkpoints](https://img.shields.io/badge/🤗%20Checkpoints-coming%20soon-yellow)](#-release-plan)

**[📑 Paper](#-updates)** · **[🧩 Method](#-method-overview)** · **[📊 Results](#-results)** · **[📋 Release Plan](#-release-plan)** · **[📝 Citation](#-citation)**

</div>

---

**EVOKE** is a post-training method that elicits the world knowledge already inside pretrained LLM agents, so that they decide by the **consequences of their actions** rather than by contextual habits, and transfer to unseen environments.

<p align="center">
  <img src="assets/overview.png" width="85%" alt="EVOKE overview">
  <br>
  <em>Figure 1: From prediction to preference. (a) World-model approaches predict action consequences before choosing an action. (b) Under single-goal supervision, a policy can fit habits that fail to transfer. (c) EVOKE instead supervises action preferences at a fixed state and history under different goals.</em>
</p>

LLM agents post-trained on a set of tasks often do well where they were trained, yet drop considerably in environments they have not seen. World-model methods address this by learning to **predict** future observations, at the cost of an extra prediction objective and errors that compound during planning. For agents acting in digital environments, however, much of this knowledge is already internalized during pretraining; the problem shifts from **acquiring** it to **eliciting** it. Typical post-training supervises each visited state under a single goal, so a policy can fit the labels by associating familiar contexts with habitual next actions.

EVOKE supplies the missing pressure through **goal diversity at fixed states**. It holds the environment state and interaction history fixed, swaps in alternative goals, and ranks the **same candidate actions** under each goal. Whenever the preferred action flips with the goal, no mapping from the context alone can rank the candidates correctly, which pushes the policy to draw on its knowledge of what each action does. At deployment, EVOKE is a standard policy: **no world-model module, no inference-time planning, and no annotator**.

## 📰 Updates

- **`2026-09`**: 🏠 Repository created. Paper, code, checkpoints, and data are coming soon.

## ✨ Highlights

- 🚀 **Best across the board** — best average on ALFWorld, WebShop, and search-based QA with all three backbones.
- 🌍 **Transfers to unseen environments** — **91.1% / 93.1% / 84.6%** on unseen ALFWorld games (Qwen2.5-3B / 7B / Qwen3-1.7B).
- 🧠 **Elicits, not adds, knowledge** — the backbone already encodes action consequences; EVOKE makes the policy decide by the goal rather than by habit.

## 🧩 Method Overview

<p align="center">
  <img src="assets/pipeline.png" width="100%" alt="EVOKE training loop">
  <br>
  <em>Figure 2: The EVOKE training loop. At collected states, actions are executed and assessed under alternative goals with the state, history, and available actions fixed. The policy learns by contrastive ranking on aggregated preferences; actions can switch between positive and competing across goals.</em>
</p>

1. **Policy rollout** — the current policy interacts with the environment to collect states and interaction histories.
2. **Goal intervention** — at each collected state, the original goal is kept and alternative goals achievable from the same state are added; the state, history, and available actions stay identical across goals.
3. **Action re-evaluation** — candidate actions are executed from the same state and labeled under each goal as advancing it or not, grounded in the observed outcome.
4. **Iterative preference learning** — the policy is trained by contrastive ranking against its own favored mistakes, and each round aggregates data from all previous rounds.

## 📊 Results

<p align="center">
  <img src="assets/main_results.png" width="100%" alt="Main results on ALFWorld, WebShop, and search-based QA">
  <br>
  <em>Main results on ALFWorld and WebShop (left) and search-based QA (right) across three backbones.</em>
</p>

<p align="center">
  <img src="assets/unseen_results.png" width="85%" alt="ALFWorld unseen results">
  <br>
  <em>Generalization to unseen ALFWorld games.</em>
</p>

## 📋 Release Plan

> **Last updated**: 2026-09-29

- [ ] Paper on arXiv
- [ ] Training and evaluation code (ALFWorld, WebShop, search-based QA)
- [ ] Trained checkpoints (LoRA adapters)
- [ ] Goal-intervention preference data
- [ ] Scripts to reproduce the main results and analyses

## 📝 Citation

The BibTeX entry will be added once the paper is available on arXiv.

## 📬 Contact

Questions and suggestions are welcome — please open an [issue](../../issues).
