# Waggle RLM-style Benchmark Results

> **Warning:** This benchmark follows the benchmark families used in the RLM paper,
> but uses deterministic synthetic memory tasks mapped to Waggle's graph/transcript
> environment. It should **not** be compared numerically to the RLM paper until the
> exact public datasets and matching model setup are run.

| Benchmark family | Scale | Method | Score | F1 | Ev. Coverage | Tokens returned | Latency (ms) |
|---|---:|---|---:|---:|---:|---:|---:|
| S-NIAH-style | 128 | raw_context | 1.000 | 1.000 | 1.000 | 1423 | 4 |
| S-NIAH-style | 128 | query_graph | 1.000 | 1.000 | 1.000 | 93 | 5 |
| S-NIAH-style | 128 | build_context | 1.000 | 1.000 | 1.000 | 181 | 22 |
| S-NIAH-style | 512 | raw_context | 1.000 | 1.000 | 1.000 | 1444 | 7 |
| S-NIAH-style | 512 | query_graph | 1.000 | 1.000 | 1.000 | 93 | 15 |
| S-NIAH-style | 512 | build_context | 1.000 | 1.000 | 1.000 | 201 | 81 |
| S-NIAH-style | 2048 | raw_context | 1.000 | 1.000 | 1.000 | 1430 | 30 |
| S-NIAH-style | 2048 | query_graph | 1.000 | 1.000 | 1.000 | 94 | 52 |
| S-NIAH-style | 2048 | build_context | 1.000 | 1.000 | 1.000 | 202 | 242 |

## Token efficiency: build_context vs baselines

| Benchmark family | Scale | Method | Tokens returned | Score |
|---|---:|---|---:|---:|
| S-NIAH-style | 128 | query_graph | 93 | 1.000 |
| S-NIAH-style | 128 | build_context | 181 | 1.000 |
| S-NIAH-style | 128 | raw_context | 1423 | 1.000 |
| S-NIAH-style | 512 | query_graph | 93 | 1.000 |
| S-NIAH-style | 512 | build_context | 201 | 1.000 |
| S-NIAH-style | 512 | raw_context | 1444 | 1.000 |
| S-NIAH-style | 2048 | query_graph | 94 | 1.000 |
| S-NIAH-style | 2048 | build_context | 202 | 1.000 |
| S-NIAH-style | 2048 | raw_context | 1430 | 1.000 |
