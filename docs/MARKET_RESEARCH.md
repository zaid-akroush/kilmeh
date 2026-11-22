# Kilmeh: market and landscape research

Current as of 2026-11-22. Merged from five research passes (2026-11-10 to 2026-11-22), all done by research agents reading web pages. No human has read the sources yet. Items marked **verify** rest on secondary or low-quality sources, search snippets, or pages that could not be opened. Check them against primary sources before citing them anywhere.

## 1. Summary

- **What Kilmeh covers that nobody else does:** browser-graded right-to-left (RTL) UI tasks, mixed Arabic/English (bidi) text in generated UIs, dialect and Arabizi prompts approved by a native speaker, and Arabic text kept byte-for-byte through agent edits. No other benchmark found tests coding agents on any of these.
- **What is not new:** Arabic coding-agent tasks exist. LILT's Terminal-Bench-LILT has 30 closed Arabic tasks with a public leaderboard, and LILTBench has 7 open, runnable Arabic terminal tasks in MSA. Afandem measures dialect and Arabizi parity, but for service agents, not coding agents. Kilmeh does not claim to be the first Arabic agent benchmark or the first Arabic leaderboard.
- **Existing Arabic code evaluations are function-level and translated** (3LM, QIMMA): no repo, no tools, no UI.
- **Prompt language is the weakest claim.** LILT found that native-language instructions moved results by at most about 7 points in German, Hindi and Chinese. Arabic dialects and Arabizi were not tested. Kilmeh's first run (`results/v1-run-2026-11.md`) saw a gap for Arabizi on 4 tasks, which is too small to claim.
- **The loudest user complaint is bidi text shown in the wrong order**, mostly in the agents' own interfaces. Kilmeh cannot grade those interfaces, but it can grade the same mistakes in UIs the agents build (section 4).

## 2. Neighbours

### 2.1 Arabic LLM benchmarks (knowledge and code generation)

| Project | What it is | Gap vs. Kilmeh |
|---|---|---|
| [3LM](https://arxiv.org/pdf/2507.15850) ([HF blog](https://huggingface.co/blog/tiiuae/3lm-benchmark), [ACL](https://aclanthology.org/2025.arabicnlp-main.4/)) | Arabic STEM and code. Code part is HumanEval+ and MBPP+ translated to Arabic with human review. | Function-level, single-turn, no agent, no repo, no UI |
| [QIMMA](https://huggingface.co/blog/tiiuae/qimma-arabic-leaderboard) ([code eval, arXiv 2604.03395](https://arxiv.org/abs/2604.03395)) | Arabic LLM leaderboard including the 3LM code tasks. Says coding is the hardest domain for Arabic-specialised models. | Same; model-only |
| [HELM Arabic Enterprise](https://crfm.stanford.edu/2026/05/26/helm-arabic-enterprise.html) | Stanford CRFM with Arabic.AI, 2026-05: business tasks such as UAE legal QA and finance | No code track |
| [IEEE: Arabic prompts to Python](https://ieeexplore.ieee.org/abstract/document/10638877/) | ChatGPT-3.5/4 and Gemini generating Python from Arabic prompts | Early models, small, no agents |
| [Arabic Prompts with English Tools](https://arxiv.org/abs/2601.05101) | Arabic tool calling; reports 5 to 10% accuracy drops | Not coding |
| [Arabic LLM benchmark survey](https://arxiv.org/pdf/2510.13430) | Survey of benchmarks and gaps | Survey only |

### 2.2 Agentic coding benchmarks

| Project | What it is | Gap vs. Kilmeh |
|---|---|---|
| [Terminal-Bench-LILT](https://arxiv.org/abs/2608.28641) ([repo](https://github.com/lilt/terminal-bench-lilt), [blog](https://lilt.com/blog/terminal-bench-lilt-multilingual-coding-benchmark)) | 300 terminal tasks in 10 languages, 30 Arabic, native-written, Harbor format. Tasks held out; repo has no open licence. Scores on the [AURORA leaderboard](https://aurora.lilt.com/), which has an Arabic column. | Outsiders cannot run the Arabic tasks. Terminal only: no browser RTL UI, no dialect or Arabizi. |
| [LILTBench](https://github.com/lilt/liltbench-tasks-public) ([blog](https://lilt.com/blog/liltbench-hackathon-multilingual-model-benchmark)) | Apache-2.0, 93 community tasks in 31 languages, run with Harbor. 7 Arabic: hamza normalisation, Hijri dates, joining forms, Saudi addresses and others. | Open and runnable, but MSA, terminal and file tasks only; tests locale logic, not whether an agent corrupts existing Arabic. |
| [Afandem (أفندم)](https://github.com/1AyaNabil1/Afandem) ([DOI](https://doi.org/10.5281/zenodo.23986571)) | Same request in English, MSA, Egyptian, Arabizi and two code-switched forms, scored programmatically, native-written. Pilot, no results yet (2026-11-16). | Service agents (clinic, telecom, banking), Egyptian. Kilmeh: coding agents, Jordanian. Complementary. |
| [RuBench](https://arxiv.org/abs/2607.06411) | 25 repo tasks written natively in Russian; withheld tests with a SHA-256 manifest | Russian only. A model for held-out policy. |
| [Multi-SWE-bench](https://arxiv.org/pdf/2504.02605), [SWE-bench Multilingual](https://evalscope.readthedocs.io/zh-cn/latest/benchmarks/swe_bench_multilingual_agentic.html) | Many programming languages, English issue text | Vary the programming language, not the natural language |
| [WebMMU](https://arxiv.org/abs/2508.16763) | Multilingual web QA, HTML/CSS/JS editing, mockup-to-code | No RTL-specific scoring found (**verify**) |
| [Arabic function-calling set](https://mosescreates-arabic-agent-eval-leaderboard.static.hf.space/index.html) | One-person set, 75 items, includes Arabizi and bidi cases, no stated licence | Not coding |

### 2.3 RTL UI evaluation

- **No automated RTL UI benchmark was found** in any pass, up to 2026-11-22. FrontendBench ([arXiv 2506.13832](https://arxiv.org/abs/2506.13832)) has no RTL.
- **Informal only:** Artificial Analysis MicroEvals ([one](https://artificialanalysis.ai/microevals/badilak-arabi--professional-frontend-engineering-challenge-v1-1793419814620), [two](https://artificialanalysis.ai/microevals/badilak-arabi--professional-frontend-engineering-challenge-v1-1793392798532)) compare models on one Arabic RTL frontend prompt, judged by a model.
- "RTL" in hardware papers (TuRTLe, RTLLM) means register-transfer level. Not relevant.

## 3. Known agent failure modes in RTL work

Practitioner sources, thin evidence:

- Physical CSS (`margin-left`, `ml-4`) where logical CSS (`margin-inline-start`, `ms-4`) is needed ([VP0](https://vp0.com/blogs/fixing-arabic-rtl-flexbox-ai-react-native), [Dev.to](https://dev.to/idanlevi1/ai-coding-agents-are-great-but-they-suck-at-rtl-heres-how-i-fixed-it-2g0g)).
- Double flip from `flex-direction: row-reverse` under RTL ([VP0](https://vp0.com/blogs/fixing-arabic-rtl-flexbox-ai-react-native)).
- Mirroring numbers and media controls, or not mirroring navigation and directional icons ([Translated](https://translated.com/resources/arabic-rtl-market-localization-mistakes)).
- Bidi corruption in mixed strings and punctuation ([CallSphere](https://callsphere.ai/blog/building-rtl-compatible-agent-interfaces-arabic-hebrew-persian.md)).

Kilmeh's v1.0 run saw the first one directly: an agent swapped `padding-left` for `inset-inline-start`, which does not replace padding (`results/v1-run-2026-11.md`, section 4).

## 4. Demand

- **Mixed Arabic/English text in the wrong order is the most reported problem.** Reports cover Claude Code, Cursor, Codex and DeepSeek, for example [claude-code #76712](https://github.com/anthropics/claude-code/issues/76712), [#48559](https://github.com/anthropics/claude-code/issues/48559), [#54666](https://github.com/anthropics/claude-code/issues/54666), [#38005](https://github.com/anthropics/claude-code/issues/38005), [openai/codex #19504](https://github.com/openai/codex/issues/19504), [DeepSeek-V3 #1662](https://github.com/deepseek-ai/DeepSeek-V3/issues/1662), [Cursor forum 1](https://forum.cursor.com/t/arabic-english-mixed-text-is-visually-reordered-incorrectly-in-cursor-chat-rtl-ltr-issue/152615), [Cursor forum 2](https://forum.cursor.com/t/arabic-rtl-chat-text-renders-with-broken-bidi-layout-on-windows/162815), [microsoft/terminal #20302](https://github.com/microsoft/terminal/issues/20302). These count complaints, not bug rates (**verify**). The root causes (no `dir="auto"`, no `<bdi>` or Unicode isolates, forced `unicode-bidi` overrides) are mistakes an agent can also make in UIs it builds. Kilmeh added three bidi tasks for this (v1.1).
- **Agents corrupting non-English text when editing files:** [OpenAI forum report](https://community.openai.com/t/bug-report-non-english-characters-corruption-when-editing-code-in-gpt-codex/1356678) (Polish, Windows). This is what Track B measures.
- **Arab labs name agentic Arabic work and dialects as weak spots.** Jais 3 scored about 64% on an Arabic file-processing eval against about 96% for a leading closed model; its developers call dialects "the hardest frontier" ([Khaleej Times](https://www.khaleejtimes.com/uae/abu-dhabi-arabic-ai-jais-3-dialects)). Jais 3 reports English Terminal-Bench and SWE-bench numbers ([HPCwire](https://www.hpcwire.com/aiwire/2026/10/16/mbzuai-and-inception42-introduce-jais-3-and-arabic-speech-recognition-model/), numbers conflict, **verify**).
- **Policy pull:** the [UAE Design System](https://designsystem.gov.ae/guidelines/frontend-development) requires federal sites to support Arabic and English with mirrored layouts. A Saudi mandate is **verify**.
- **Adoption:** a JetBrains survey, [reported by Gulf News](https://gulfnews.com/technology/90-of-developers-surveyed-now-use-ai-coding-agents-at-work-jetbrains-says-1.500700542), says 90% of surveyed developers use coding agents weekly (global; primary page not opened, **verify**). Arabic.AI and Replit run [free Arabic coding courses](https://www.wamda.com/en/2026/01/arabicai-launches-free-arabic-coding-courses-partnership-replit) across MENA.
- **No vendor claims:** no official Anthropic or OpenAI documentation of Arabic or RTL quality for their coding agents was found (**verify**).

## 5. Arabizi

- No benchmark of coding agents with Arabizi prompts was found (shallow search: "none found", not "none exist").
- Prior work: AladdinBench ([arXiv 2502.20973](https://arxiv.org/abs/2502.20973), Lebanese, Egyptian, Algerian, gated). VARabiziLex/VARabiziCues ([arXiv 2608.02555](https://arxiv.org/abs/2608.02555), five dialects, none Jordanian). ATAR ([Zenodo](https://zenodo.org/record/4942919)): Jordanian, 25k+ pairs, CC BY 4.0, no data download found. The Talafha, Abu Ammar and Al-Ayyoub Jordanian corpus (IJECE 2021) is on GitHub with no licence, so it cannot be reused without permission. All **verify**.
- Language-ID tools tend to label Arabizi as English (**verify**). This matters for Track D.
- Policy: these are spelling references for native authors only. No sentence is copied into a task. Kilmeh grows its own spelling data through the [contributor site](https://kilmeh.github.io/contribute).

## 6. How benchmarks get adopted

- Labs report benchmarks that are hard, backed by a named institution, and easy to run. Terminal-Bench launched with 89 tasks and a large author list ([paper](https://arxiv.org/abs/2601.11868)).
- [Harbor](https://docs.harborframework.com/harbor-hub/leaderboards.md) is the common format and the official Terminal-Bench 2.0 harness ([tbench docs](https://tbench.ai/docs)). Anyone can publish a dataset and leaderboard on its hub. Kilmeh exports to Harbor.
- The Arabic evaluation community expects a Hugging Face dataset and leaderboard Space.
- A small single-author benchmark will not be reported by frontier labs. Realistic first users: Arabic labs, researchers, and Arabic app builders.
- Venues and funding: [Snorkel Open Benchmarks Grants](https://benchmarks.snorkel.ai/) (in-kind, rolling, open release required). ArabicNLP 2026 deadlines have passed ([CFP](https://www.aclweb.org/portal/node/14460)); next target ArabicNLP 2027 or an agents/evaluation workshop.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Machine-translated prompts are unnatural | Native authoring only; agents never write final Arabic or Arabizi |
| Visual RTL bugs missed by text-only checks | Real-browser checks of computed style, element boxes and rendered order |
| Harness differences hide model differences | Report agent and model separately; hold the model fixed when comparing agents |
| Contamination once tasks are public | Private held-out split, versioned task sets |
| Agent nondeterminism | Several tries, Wilson intervals, paired tests; each write-up fixes its claims before results |
| One native speaker, one dialect | Stated as a limitation; contributor site; second reviewer planned |
| A funded lab covers the same ground | Stay open, runnable by anyone, and deep on RTL, bidi, dialect and byte integrity |
