<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/title-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/title-light.svg">
    <img alt="Mithil Salunkhe" src="assets/title-light.svg" width="100%">
  </picture>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/skyline-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/skyline-light.svg">
    <img alt="The last twelve months of contributions as an axonometric city, one tower per day" src="assets/skyline-light.svg" width="100%">
  </picture>
  <br>
  <a href="https://www.kaggle.com/mithilsalunkhe">Kaggle</a> ·
  <a href="https://x.com/mithil_salunkhe">X</a> ·
  <a href="https://orcid.org/0009-0003-4106-6962">ORCID</a> ·
  <a href="mailto:mithils3@illinois.edu">mithils3@illinois.edu</a>
</div>

<br>

Sophomore at the University of Illinois studying computer science. I build evaluation infrastructure for AI agents and train models on GPU clusters. Most of my time goes to one question. When an agent says it succeeded, how do you check?

## Now

**[RECLAIM](https://github.com/mithils3/reprocli)** measures whether AI agents can reproduce published ML research. Each of 100 NeurIPS 2025 papers is frozen to one target claim, a numeric tolerance, and a metered GPU-hour budget. A reproduction agent runs the experiment in an Apptainer sandbox on DeltaAI GH200 nodes, and a second pinned agent audits every run against its own execution evidence, because agents routinely report a success their logs do not support. 827 commits since June 1. Writing it up for ICLR.

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/compute-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/compute-light.svg">
    <img alt="RECLAIM metered compute: cumulative H100-hours across reproduction runs" src="assets/compute-light.svg" width="100%">
  </picture>
</div>

**[pl-cal](https://github.com/mithils3/pl-cal)** turns PrairieLearn deadlines and PrairieTest exam slots into a calendar you can subscribe to. Chrome extension, no server.

**AIS at Illinois.** Exec this semester, running the technical track.

## Selected work

| Project | What it is |
| --- | --- |
| [reprocli](https://github.com/mithils3/reprocli) | The RECLAIM harness. Slurm scheduler, Apptainer sandbox, run store, trajectory viewer. |
| [reclaim](https://github.com/mithils3/reclaim) | Anonymized code and data release for the paper. |
| [SainaRanesk](https://github.com/mithils3/SainaRanesk) | RadioScribe. Offline Chinese to English speech pipeline for noisy military radio, built on Qwen3-ASR and vLLM with denoising and diarization. |
| [pl-cal](https://github.com/mithils3/pl-cal) | PrairieLearn deadlines to an ICS feed, shipped as a Chrome extension. |
| [Financial-Reasoning-LLM](https://github.com/mithils3/Financial-Reasoning-LLM) | Reasoning fine-tunes on financial question answering. |

## Competitions

- **1st of 5,000** in the AI/ML track, [Sainya Ranakshetram 2.0](https://www.sainya-ranakshetram.in/), Indian Army
- **2nd** in the [Wadhwani AI Bollworm Counting Challenge](https://zindi.africa/competitions/wadhwani-ai-bollworm-counting-challenge) on Zindi
- **3rd** in the Trustii [AllergenChip Challenge](https://github.com/Trustii-team/AllergenChip)
- **Kaggle Expert** with three competition silvers. [G2Net](https://www.kaggle.com/competitions/g2net-gravitational-wave-detection), [PetFinder Pawpularity](https://www.kaggle.com/competitions/petfinder-pawpularity-score), [Contrails](https://www.kaggle.com/competitions/google-research-identify-contrails-reduce-global-warming)

## Stack

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/stack-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/stack-light.svg">
  <img alt="Python, PyTorch, C++, TypeScript, CUDA, Slurm, Apptainer, vLLM, Supabase, three.js" src="assets/stack-light.svg">
</picture>

---

<sub>Everything above is generated from live data by [`scripts/`](scripts) and committed by [a workflow](.github/workflows/assets.yml). The vector assets are hand-rendered SVG that carry their own CSS motion, honor `prefers-reduced-motion`, and stay legible with animation off. The 3D hero is projected and depth-sorted in Python and written out as vector polygons with flat-shaded faces, so it is exact at any zoom and on any display.</sub>
