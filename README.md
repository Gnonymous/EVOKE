<div align="center">

# EVOKE: Eliciting World Knowledge in Agents for Transferable Decision-Making

**Yuhan Guo**<sup>1</sup>, **Jinming Liu**<sup>1</sup>, **Liang Xu**<sup>1</sup>, **Ziqiang Li**<sup>1</sup>, **Jianguo Huang**<sup>1</sup>, **Zhicheng Wang**<sup>2</sup>,<br>
**Hu Zhu**<sup>2</sup>, **Qiuyu Chen**<sup>1</sup>, **Yuntao Wei**<sup>2</sup>, **Xin Jin**<sup>3</sup>, **Wenjun Zeng**<sup>3</sup>

<sup>1</sup>Shanghai Jiaotong University &nbsp; <sup>2</sup>Hong Kong Polytechnic University &nbsp; <sup>3</sup>Eastern Institute of Technology, Ningbo

[![Paper](https://img.shields.io/badge/arXiv-coming%20soon-b31b1b?logo=arxiv&logoColor=white)](#)
[![Code](https://img.shields.io/badge/Code-coming%20soon-lightgrey?logo=github)](#release-plan)

</div>

> [!NOTE]
> Code, checkpoints, and experiment scripts are **coming soon**. Watch this repository for updates; this README is the single place where release status and links are maintained.

<p align="center">
  <img src="assets/overview.png" alt="EVOKE overview" width="70%"/>
</p>

## TL;DR

LLM agents already carry much of the knowledge about what their actions do from pretraining; the problem is getting the policy to *use* it when deciding. **EVOKE** holds the state and interaction history fixed, swaps in alternative goals, and trains the policy to rank the same candidate actions under each goal. When the preferred action flips with the goal, a policy that relies on contextual habits cannot rank correctly, so it is pushed to draw on its knowledge of action consequences. No world-model module, no prediction objective, and no inference-time planning are needed.

## Abstract

Large language models (LLMs) are increasingly deployed as agents for multi-step decision-making, yet transfer poorly to unseen environments. World-model methods address this by training agents to predict future observations, at the cost of additional training and errors that compound when predictions are used for planning. However, for LLM agents operating in digital environments, much of this world knowledge is already internalized during pretraining, which shifts the problem from acquiring it to eliciting it. We argue that typical post-training provides little pressure for such elicitation, since supervision under a single goal at each visited state inadvertently drives policies to rely on superficial contextual habits. We introduce **EVOKE**, a post-training method that supplies this pressure through goal diversity at fixed states. Motivated by theory showing that an agent competent across diverse goals must encode a world model recoverable from its action preferences, EVOKE holds the environment state and interaction history fixed and ranks the same candidate actions under alternative goals, forcing action preferences to change, so that a policy relying on contextual habits or single-goal correlations cannot order them correctly. This implicitly elicits the policy's pretrained world knowledge to inform decisions. We evaluate EVOKE across diverse tasks in three backbones, demonstrating improved task performance, unseen environment generalization, and data efficiency. We further conduct controlled analyses to better understand what drives these gains. These findings offer a new perspective on eliciting internalized world knowledge for transferable action through direct decision supervision.

## Method

<p align="center">
  <img src="assets/pipeline.png" alt="EVOKE training loop" width="100%"/>
</p>

EVOKE repeats four stages: **(1)** roll out the current policy to collect states; **(2)** at each state, keep the original goal and add alternative goals achievable from the same state; **(3)** execute candidate actions from the same state and label them under each goal; **(4)** train the policy with contrastive ranking against its own preferred mistakes, aggregating data across rounds. At deployment, EVOKE is a standard policy.

## News

- **[2026-09]** Paper coming soon on arXiv.

## Release Plan

- [ ] Paper on arXiv
- [ ] Training and evaluation code (ALFWorld, WebShop, search-based QA)
- [ ] Trained checkpoints (LoRA adapters)
- [ ] Goal-intervention preference data
- [ ] Experiment scripts for the main results and analyses

## Citation

A BibTeX entry will be added once the arXiv version is available.

## Contact

For questions, please open an [issue](../../issues).
