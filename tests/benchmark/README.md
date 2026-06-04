# ZEA Benchmark Suite

Measures how accurately ZEA detects languages, frameworks, and architecture nodes in real open-source repositories.

---

## Running Benchmarks

**Quick** (no network — uses repos already cloned to `/tmp/zea_benchmarks/`):
```bash
python -m tests.benchmark.runner --quick
```

**Full** (clones all repos, takes ~5 minutes):
```bash
python -m tests.benchmark.runner --all
```

**Single repo:**
```bash
python -m tests.benchmark.runner --repo https://github.com/tiangolo/fastapi
```

Results are saved to `benchmark_results.json` (override with `--output <path>`).

---

## Smoke Test (no network, fast)

```bash
pytest tests/benchmark/test_benchmark_smoke.py -v
```

Creates a synthetic FastAPI repo in a temp directory, runs ZEA on it, and verifies basic correctness. Should always pass.

---

## Benchmark Targets

| Repo | Language | Framework | What it tests |
|------|----------|-----------|---------------|
| tiangolo/fastapi | Python | FastAPI | REST API detection, Python inference |
| django/django | Python | Django | Large Python monorepo |
| expressjs/express | JavaScript | Express | JavaScript framework inference |
| nestjs/nest | TypeScript | NestJS | TypeScript detection |
| gothinkster/node-express-realworld-example-app | JavaScript | Express | Full-stack: Express + MongoDB |
| spring-projects/spring-petclinic | Java | Spring | Java/Spring Boot detection |

---

## Scores Explained

### Precision
> Of all the items ZEA detected, what fraction were correct?

`precision = correct_detections / total_detections`

High precision means ZEA doesn't invent things that aren't there.

### Recall
> Of all the items ZEA should have detected, what fraction did it find?

`recall = found_expected / total_expected`

High recall means ZEA doesn't miss things that are there.

### F1 Score
> The harmonic mean of precision and recall. Penalizes imbalance.

`f1 = 2 * precision * recall / (precision + recall)`

F1 is the primary per-category metric.

### Graph Node Types Score
> Fraction of expected node type requirements met.

For example, if the ground truth says "at least 1 `database` node", and ZEA finds one, that requirement is met. The score is `requirements_met / total_requirements`.

### Overall Score
> Average of inventory overall (language F1 + framework F1 + has_tests) and graph overall (node type requirements met).

```
overall = (inventory_overall + graph_overall) / 2
```

### What "Good" Looks Like

| Overall Score | Grade |
|---------------|-------|
| >= 0.85 | Excellent — ZEA is reliably detecting architecture |
| 0.70 – 0.84 | Decent — most things detected, some gaps |
| 0.50 – 0.69 | Needs work — significant misses or false positives |
| < 0.50 | Poor — fundamental detection issues |

---

## Adding New Targets

Edit `tests/benchmark/targets.py` and add a `BenchmarkTarget` to `BENCHMARK_TARGETS`:

```python
BenchmarkTarget(
    repo_url="https://github.com/org/repo",
    description="What this repo tests",
    expected_languages=["python"],
    expected_frameworks=["flask"],
    expected_node_types={"repository": 1, "backend": 1, "database": 1},
    expected_has_tests=True,
)
```

Ground truth should reflect what ZEA *should* detect, not necessarily every aspect of the repo.
