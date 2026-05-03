# Waggle RLM-style Benchmark Results

> **Warning:** This benchmark follows the benchmark families used in the RLM paper,
> but uses deterministic synthetic memory tasks mapped to Waggle's graph/transcript
> environment. It should **not** be compared numerically to the RLM paper until the
> exact public datasets and matching model setup are run.

| Benchmark family | Scale | Method | Score | F1 | Ev. Coverage | Tokens returned | Latency (ms) |
|---|---:|---|---:|---:|---:|---:|---:|
| OOLONG-Pairs-style | 128 | raw_context | 0.000 | 0.000 | 0.000 | 1422 | 4 |
| OOLONG-Pairs-style | 128 | query_graph | 0.000 | 0.000 | 0.000 | 98 | 5 |
| OOLONG-Pairs-style | 128 | build_context | 1.000 | 1.000 | 1.000 | 515 | 21 |
| OOLONG-Pairs-style | 512 | raw_context | 0.000 | 0.000 | 0.000 | 1390 | 8 |
| OOLONG-Pairs-style | 512 | query_graph | 0.000 | 0.000 | 0.000 | 98 | 15 |
| OOLONG-Pairs-style | 512 | build_context | 1.000 | 1.000 | 1.000 | 435 | 86 |
| OOLONG-Pairs-style | 2048 | raw_context | 0.000 | 0.000 | 0.000 | 1407 | 30 |
| OOLONG-Pairs-style | 2048 | query_graph | 0.000 | 0.000 | 0.000 | 98 | 58 |
| OOLONG-Pairs-style | 2048 | build_context | 1.000 | 1.000 | 1.000 | 541 | 258 |

## Token efficiency: build_context vs baselines

| Benchmark family | Scale | Method | Tokens returned | Score |
|---|---:|---|---:|---:|
| OOLONG-Pairs-style | 128 | query_graph | 98 | 0.000 |
| OOLONG-Pairs-style | 128 | build_context | 515 | 1.000 |
| OOLONG-Pairs-style | 128 | raw_context | 1422 | 0.000 |
| OOLONG-Pairs-style | 512 | query_graph | 98 | 0.000 |
| OOLONG-Pairs-style | 512 | build_context | 435 | 1.000 |
| OOLONG-Pairs-style | 512 | raw_context | 1390 | 0.000 |
| OOLONG-Pairs-style | 2048 | query_graph | 98 | 0.000 |
| OOLONG-Pairs-style | 2048 | build_context | 541 | 1.000 |
| OOLONG-Pairs-style | 2048 | raw_context | 1407 | 0.000 |
