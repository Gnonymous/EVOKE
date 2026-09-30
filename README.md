

![EVOKE logo](assets/logo.png)

# EVOKE: Eliciting World Knowledge in Agents for Transferable Decision-Making

![Project Page](https://img.shields.io/badge/Project-Page-007BFF?logo=googlechrome&logoColor=white)
![arXiv](https://img.shields.io/badge/arXiv-coming%20soon-b31b1b.svg?logo=arxiv&logoColor=white)
![Model](https://img.shields.io/badge/🤗%20Model-Hugging%20Face-yellow)

**[🌐 Project Page](https://gnonymous.github.io/EVOKE)** · **[📑 Paper](#-updates)** · **[💡 Motivation](#-motivation)** · **[📊 Results](#-results)** · **[📋 Release Plan](#-release-plan)** · **[📝 Citation](#-citation)**



---

**EVOKE** is a post-training method that elicits the world knowledge already inside pretrained LLM agents, so that they decide by the **consequences of their actions** rather than by contextual habits. It holds the state fixed, swaps in alternative goals, and trains the policy to rank the **same candidate actions** under each goal, with no world-model module and no inference-time planning.

![EVOKE training loop](assets/pipeline.png)  
*The EVOKE training loop. At collected states, actions are executed and assessed under alternative goals with the state, history, and available actions fixed. The policy learns by contrastive ranking on aggregated preferences; actions can switch between positive and competing across goals.*

## 📰 Updates

- `2026-09`: 🏠 Repository and [project page](https://gnonymous.github.io/EVOKE) are live. Paper, code, models, and data are coming soon.



## ✨ Highlights

- 🚀 **Best across the board** — best average on ALFWorld, WebShop, and search-based QA with all three backbones.
- 🌍 **Transfers to unseen environments** — **91.1% / 93.1% / 84.6%** on unseen ALFWorld games (Qwen2.5-3B / 7B / Qwen3-1.7B).
- 🧠 **Elicits, not adds, knowledge** — the backbone already encodes action consequences; EVOKE makes the policy decide by the goal rather than by habit.



## 💡 From Prediction to Preference


|                                                       |     |
| ----------------------------------------------------- | --- |
| ![From prediction to preference](assets/overview.png) |     |


**Do agents need to *predict* consequences to use them?**

**(a) Predict consequences.** World models learn to predict future observations, adding cost and compounding errors in planning.

**(b) Single-goal supervision.** The knowledge is already in pretrained LLMs, but one goal per state lets the policy fit habits that fail to transfer.

**(c) EVOKE.** Change the goal at a fixed state. Preferences flip, so habits fail and the policy must use its knowledge of consequences.



## 📊 Results



### Main Results

![Main results on ALFWorld, WebShop, and search-based QA](assets/main_results.png)  
*Main results on ALFWorld and WebShop (left) and search-based QA (right) across three backbones.*

![ALFWorld unseen results](assets/unseen_results.png)  
*Generalization to unseen ALFWorld games.*

### Analysis

All analyses use Qwen2.5-3B on ALFWorld unless noted.

![Decision-supervision ablations](assets/ablations.png)  
***Decision-supervision ablations.** Removing alternative goals or replacing ranking with imitation hurts unseen success. Micro success (%) and average unseen steps, averaged over training seeds.*


|                                                               |                                                                   |
| ------------------------------------------------------------- | ----------------------------------------------------------------- |
| ![Data efficiency](assets/data_efficiency.png)                | ![Iterative improvement](assets/iteration.png)                    |
| ***Data efficiency.** EVOKE outperforms SFT at every budget.* | ***Iterative improvement.** Every round improves every backbone.* |


![From knowledge to goal-directed decisions](assets/knowledge_use.png)  
***From knowledge to goal-directed decisions.** (a) Action consequences are linearly decodable before any ALFWorld training. (b) EVOKE makes the fewest habitual errors, i.e., choosing the action that is correct for another goal in the same context.*

![Execution on unseen games](assets/execution.png)  
***Execution on unseen games.** EVOKE succeeds earlier and wastes fewer actions: (a) cumulative success over steps, (b) invalid actions per game, (c) revisits per successful game.*

## 📋 Release Plan

> **Last updated**: 2026-09-29

- [ ] Paper on arXiv
- [ ] Training and evaluation code (ALFWorld, WebShop, search-based QA)
- [ ] Trained models ([Hugging Face](https://huggingface.co/Gnonymous/EVOKE))
- [ ] Goal-intervention preference data
- [ ] Scripts to reproduce the main results and analyses



## 📝 Citation

The BibTeX entry will be added once the paper is available on arXiv.

## 📬 Contact

Questions and suggestions are welcome — please open an [issue](../../issues).