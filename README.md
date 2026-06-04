# ZEA — Zealous Engine for Architectures

**Turn any repository into a living 3D architecture graph**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()

---

## What is ZEA?

ZEA is an **Architecture Intelligence Engine**. Point it at any software repository and it produces:

- **Architecture Knowledge Graph** — services, APIs, databases, events, infrastructure as a connected graph
- **3D Interactive System Design** — a Three.js scene with 3D components on a dark surface, wired & wireless connections
- **AI Architecture Analysis** — Claude analyzes the codebase and enriches the graph with descriptions, capabilities, domains
- **Slash Commands for Claude Code** — `/system-design`, `/service-map`, `/data-flow`, `/domain-map`, `/impact-analysis`

> *"I just joined this project. How does this system work?"*
> That question — answered in seconds, not weeks.

---

## Quick Start

```bash
pip install zea

# Static analysis (no API key needed)
zea analyze /path/to/your/repo
zea visualize .zea/architecture_graph.json

# AI-powered full pipeline
export ANTHROPIC_API_KEY=your_key_here
zea ai-analyze /path/to/your/repo
open .zea/architecture.html
```

---

## The 3D System Design

ZEA renders architecture as a proper system design scene — not a floating sphere graph:

| Element | What it represents |
|---------|-------------------|
| Dark surface + grid | Deployment environment |
| Cubes | Services and backends |
| Cylinders | Databases and caches |
| Torus rings | Message queues (Kafka, RabbitMQ, SQS) |
| Octahedra | Domain events |
| Wide flat boxes | Frontends and gateways |
| Spheres | External systems (Stripe, Salesforce) |
| Tube curves | Wired connections (HTTP calls, DB queries) |
| Dashed arcs + signal rings | Wireless connections (events, pub-sub) |

---

## Pipeline

```
Repository
    ↓
Repository Discovery     →  repository_inventory.json
    ↓
Architecture Inference   →  architecture_graph.json
    ↓
AI Analysis (Claude)     →  architecture.json + architecture.md
    ↓
3D System Design Render  →  architecture.html
```

---

## CLI Commands

```bash
zea analyze <repo>              # Static scan → graph
zea ai-analyze <repo>           # Full AI pipeline → 3D design
zea visualize <graph.json>      # Render 3D HTML from existing graph
zea version                     # Show version
```

---

## Output Files

| File | Description |
|------|-------------|
| `repository_inventory.json` | Languages, frameworks, package managers, infrastructure |
| `architecture_graph.json` | Full knowledge graph — nodes and edges with evidence |
| `architecture.json` | AI-enriched analysis — descriptions, capabilities, domains |
| `architecture.md` | Human-readable system design document |
| `service-map.json` | Service dependency map |
| `domain-map.json` | Business domain groupings |
| `architecture.html` | **3D interactive system design** — open in any browser |

---

## Slash Commands (Claude Code)

Copy `skills/claude-code/SKILL.md` → `.claude/skills/zea/SKILL.md` in your project:

| Command | Description |
|---------|-------------|
| `/system-design` | Full 3D system design of the current repo |
| `/service-map` | Service dependencies |
| `/data-flow` | User → API → Service → Database trace |
| `/domain-map` | Business domain groupings |
| `/impact-analysis <component>` | What breaks if this changes? |
| `/architecture-review` | Coupling, anti-patterns, tech debt |

---

## What ZEA Detects

**Languages:** Python · TypeScript · JavaScript · Java · Go · C# · Rust · Kotlin · PHP · Ruby

**Frameworks:** FastAPI · Django · Flask · Next.js · React · Angular · Vue · Express · NestJS · Spring · Gin · Echo

**Infrastructure:** Docker · Kubernetes · Terraform · Helm · GitHub Actions · GitLab CI

**Databases:** PostgreSQL · MySQL · MongoDB · Redis · DynamoDB · SQLite · Elasticsearch · Cassandra

**Messaging:** Kafka · RabbitMQ · AWS SQS/SNS · NATS · Google Pub/Sub · BullMQ

---

## Benchmark Results

| Repository | Nodes | Score |
|-----------|-------|-------|
| fastapi (Python) | 109 | **100%** |
| express (JavaScript) | 40 | **100%** |
| nest (TypeScript) | 122 | **100%** |

---

## Roadmap

| Milestone | Feature | Status |
|-----------|---------|--------|
| 0–3 | CLI, Discovery, Graph, Inference | ✅ Done |
| 3.5 | AI Analysis (Claude API) | ✅ Done |
| 4–5 | Domain + Infrastructure Intelligence | 🔄 In progress |
| 6 | 3D System Design Viewer | ✅ Done |
| 7–10 | Impact Analysis, Reviews, AI Copilot, Digital Twin | ⬜ Planned |

---

## Contributing

```bash
git clone https://github.com/manish-surya-r/ZEA.git
cd ZEA
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## License

MIT — see [LICENSE](LICENSE).

Built by [manish-surya-r](https://github.com/manish-surya-r) · Zealous Engineering

> *"Today Claude understands files. Tomorrow Claude understands systems."*
