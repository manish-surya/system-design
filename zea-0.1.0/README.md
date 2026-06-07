# ZEA — Turn any repository into a living architecture graph

[![PyPI version](https://img.shields.io/pypi/v/zea?color=blue&label=PyPI)](https://pypi.org/project/zea/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/manish-surya/system-design/actions/workflows/ci.yml/badge.svg)](https://github.com/manish-surya/system-design/actions)
[![Stars](https://img.shields.io/github/stars/zealous-engineering/zea?style=social)](https://github.com/manish-surya/system-design)

**ZEA** (system-design) is an Architecture Intelligence Engine. Point it at any software repository and it produces a structured **Architecture Knowledge Graph (AKG)** — a machine-readable, visually explorable map of every service, API, database, event stream, and infrastructure component in the codebase.

> The AKG is the product. Reports, visualizations, and AI integrations are derived from it.

---

## Quick Start

```bash
# 1. Install
pip install system-design

# 2. Analyze any repository
system-design analyze /path/to/your/repo

# 3. Open the interactive 3D visualization
open .zea/architecture.html
```

That's it. ZEA walks the repository, infers the architecture, and writes three output artifacts.

---

## What system-design Detects

| Category | Examples |
|----------|---------|
| **Languages** | Python, TypeScript, Go, Java, Rust, Ruby, C#, PHP |
| **Frameworks** | FastAPI, Django, Express, Spring Boot, Rails, NestJS, Laravel |
| **Services** | Microservices, workers, gateways, monoliths |
| **APIs** | REST endpoints, GraphQL schemas, gRPC definitions, webhooks |
| **Databases** | PostgreSQL, MySQL, MongoDB, Redis, DynamoDB, Elasticsearch |
| **Messaging** | Kafka, RabbitMQ, SQS, SNS, Pub/Sub |
| **Domain Events** | Published/consumed events with producer-consumer relationships |
| **Infrastructure** | Docker, Kubernetes, Terraform, Helm charts, CI/CD pipelines |
| **External Systems** | Stripe, Salesforce, Twilio, Auth0, and other third-party integrations |

---

## Output Artifacts

| File | Description |
|------|-------------|
| `repository_inventory.json` | Languages, frameworks, package managers, documentation |
| `architecture_graph.json` | Full Architecture Knowledge Graph (nodes + edges + evidence) |
| `architecture.html` | Standalone interactive 3D visualization (Three.js, no server needed) |

All outputs are written to `.zea/` in the repository root by default. Pass `--output <dir>` to change the destination.

---

## CLI Reference

```bash
# Full analysis (inventory + graph + visualization)
system-design analyze /path/to/repo

# Graph only (skip HTML rendering)
system-design graph /path/to/repo

# Generate a human-readable architecture report
system-design report /path/to/repo

# Custom output directory
system-design analyze /path/to/repo --output /tmp/my-analysis

# Verbose mode
system-design analyze /path/to/repo --verbose
```

---

## Architecture Diagram

```
Repository on Disk
        │
        ▼
┌───────────────────┐
│  Repository       │  ← file tree walk, language detection,
│  Discovery        │    framework detection, package detection
└────────┬──────────┘
         │  repository_inventory.json
         ▼
┌───────────────────┐
│  Structural       │  ← module graph, import analysis,
│  Analysis         │    call graph, entry points
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Architecture     │  ← service detector, API detector,
│  Inference        │    database detector, event detector
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Domain           │  ← business domain boundaries,
│  Intelligence     │    team ownership, bounded contexts
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Infrastructure   │  ← Docker, Kubernetes, Terraform,
│  Intelligence     │    CI/CD, cloud resources
└────────┬──────────┘
         │
         ▼
┌───────────────────────────────────┐
│   Architecture Knowledge Graph    │
│   (NetworkX + Pydantic models)    │
└───────────┬───────────────────────┘
            │
     ┌──────┼──────┐
     ▼      ▼      ▼
  .json   .html  .md
  graph   3D viz  report
```

Every inference cites evidence: file paths, line numbers, matched patterns, and a confidence score.

---

## Graph Schema

The AKG is a directed property graph. Every node and edge is a typed Pydantic model.

### Node Types

```
Application   Frontend · Backend · Monolith · Gateway
Service       Microservice · Worker · APIService
API           REST · GraphQL · gRPC · Webhook
Database      PostgreSQL · MySQL · MongoDB · Redis · DynamoDB
Messaging     Kafka · RabbitMQ · SQS · SNS
Event         Domain events (OrderCreated, PaymentFailed, …)
Domain        Business domains (Commerce · Billing · Identity)
Infrastructure  Cluster · Namespace · Pod · LoadBalancer
Team          Ownership nodes
External      Third-party systems (Stripe · Salesforce · …)
```

### Edge Types

```
Dependency    DEPENDS_ON · IMPORTS · REFERENCES
Communication CALLS · INVOKES · CONNECTS_TO
Data          READS · WRITES · OWNS
Events        PUBLISHES · CONSUMES
Organization  CONTAINS · BELONGS_TO · OWNED_BY
```

---

## Using ZEA with AI Coding Assistants

### Claude Code

Install the ZEA skill for Claude Code:

```bash
# Run ZEA, then ask Claude Code questions about the graph
system-design analyze . --output .zea
```

Then in Claude Code: *"Read `.zea/architecture_graph.json` and tell me what databases the Order Service uses."*

See [`skills/claude-code/SKILL.md`](skills/claude-code/SKILL.md) for the full skill manifest.

### OpenAI Codex

The Codex plugin manifest is at [`skills/codex/plugin.json`](skills/codex/plugin.json).

### Gemini CLI

The Gemini plugin manifest is at [`skills/gemini/plugin.yaml`](skills/gemini/plugin.yaml).

---

## Roadmap

| Milestone | Name | Status |
|-----------|------|--------|
| 0 | CLI Framework | ⬜ Planned |
| 1 | Repository Discovery | ⬜ Planned |
| 2 | Graph Schema + Builder | ⬜ Planned |
| 3 | Architecture Inference | ⬜ Planned |
| 4 | Domain Intelligence | ⬜ Planned |
| 5 | Infrastructure Intelligence | ⬜ Planned |
| 6 | React Viewer (2D) | ⬜ Planned |
| 7 | 3D Architecture Universe | ⬜ Planned |
| 8 | Impact Analysis | ⬜ Planned |
| 9 | Architecture Reviews | ⬜ Planned |
| 10 | AI Integrations | ⬜ Planned |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| CLI | Python 3.10+, Typer, Rich |
| Models | Pydantic v2 |
| Parsing | Tree-sitter |
| Graph | NetworkX |
| Visualization | Three.js, React Flow |
| Storage | JSON (Neo4j roadmap) |

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get started, add a new detector, and submit a pull request.

---

## License

MIT — see [LICENSE](LICENSE).

Built by [Zealous Engineering](https://github.com/zealous-engineering).
