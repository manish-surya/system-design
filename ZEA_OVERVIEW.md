# system-design — Architecture Intelligence Engine

**Turn any repository into a living 3D architecture graph.**

system-design is an open-source Architecture Intelligence Engine. Point it at any codebase and it automatically discovers services, APIs, databases, events, and infrastructure — then renders them as an interactive 3D system design you can explore in your browser.

---

## Links

| | |
|---|---|
| 🐙 GitHub | [github.com/manish-surya/system-design](https://github.com/manish-surya/system-design) |
| 📦 PyPI | `pip install system-design` *(coming soon)* |
| 📄 Docs | [github.com/manish-surya/system-design/docs](https://github.com/manish-surya/system-design/tree/master/docs) |
| 🐛 Issues | [github.com/manish-surya/system-design/issues](https://github.com/manish-surya/system-design/issues) |

---

## Install

```bash
pip install system-design

# Optional: for AI-powered analysis
pip install system-design anthropic
export ANTHROPIC_API_KEY=your_key_here
```

---

## Usage

### Static Analysis (no API key needed)
```bash
# Scan any repository
system-design analyze /path/to/your/repo

# Generate 3D visualization from the graph
system-design visualize .zea/architecture_graph.json

# Open in browser
open .zea/architecture.html
```

### AI-Powered Full Pipeline
```bash
export ANTHROPIC_API_KEY=sk-ant-...

system-design ai-analyze /path/to/your/repo
open .zea/architecture.html
```

This runs the full pipeline in one command:
1. Scans languages, frameworks, package managers, infrastructure
2. Infers services, APIs, databases, events, inter-service connections
3. Sends everything to Claude — gets back component descriptions, capabilities, domains
4. Renders a 3D interactive system design

### Output Files

| File | Description |
|------|-------------|
| `repository_inventory.json` | Languages, frameworks, package managers |
| `architecture_graph.json` | Full knowledge graph |
| `architecture.json` | AI-enriched analysis |
| `architecture.md` | Human-readable system design doc |
| `service-map.json` | Service dependency map |
| `domain-map.json` | Business domain groupings |
| `architecture.html` | **3D interactive system design** ← open this |

---

## Claude Code Slash Commands

Copy the skill into your project and use directly inside Claude Code:

```bash
mkdir -p .claude/skills/system-design
curl -o .claude/skills/system-design/SKILL.md \
  https://raw.githubusercontent.com/manish-surya/ZEA/master/skills/claude-code/SKILL.md
```

Then type in Claude Code:

| Command | What it does |
|---------|-------------|
| `/system-design` | Full 3D architecture of the current repo |
| `/service-map` | Service dependencies |
| `/data-flow` | User → API → Service → Database trace |
| `/domain-map` | Business domain groupings |
| `/impact-analysis <component>` | What breaks if this changes? |
| `/architecture-review` | Coupling issues, anti-patterns, tech debt |

---

## What system-design Detects

- **Languages** — Python, TypeScript, JavaScript, Java, Go, C#, Rust, Kotlin, PHP, Ruby
- **Frameworks** — FastAPI, Django, Flask, Next.js, React, Angular, Vue, Express, NestJS, Spring, Gin
- **Databases** — PostgreSQL, MySQL, MongoDB, Redis, DynamoDB, SQLite, Elasticsearch
- **Messaging** — Kafka, RabbitMQ, AWS SQS/SNS, NATS, Google Pub/Sub
- **Infrastructure** — Docker, Kubernetes, Terraform, Helm, GitHub Actions

---

## 3D Visualization

The `architecture.html` file is completely standalone — no server needed. Open it in any browser.

| Component | 3D Shape |
|-----------|---------|
| Services / Backends | Cubes |
| Databases | Cylinders |
| Message Queues | Torus rings |
| Events | Octahedra |
| Frontends / Gateways | Wide flat boxes |
| External Systems | Spheres |
| Wired connections (HTTP, DB) | Tube curves |
| Wireless connections (events, pub-sub) | Dashed arcs |

---

## Current Status

system-design v0.1.0 is an **alpha release**. The following milestones are complete:

- ✅ CLI Framework
- ✅ Repository Discovery
- ✅ Architecture Knowledge Graph
- ✅ Architecture Inference (services, APIs, DBs, events, inter-service calls)
- ✅ AI Analysis via Claude API
- ✅ 3D System Design Viewer (Three.js)
- ✅ Claude Code Slash Commands
- ✅ Codex + Gemini CLI plugins
- ✅ Benchmark suite (100% on fastapi, express, nestjs)

---

## Roadmap

A complete, production-ready version of ZEA — including Impact Analysis, Architecture Reviews, AI Copilot Interface, Domain Intelligence, and the Software Digital Twin — **will be released by end of June 2026**.

The full release will include:
- Impact analysis ("what breaks if I change X?")
- Architecture review engine (coupling, anti-patterns, tech debt scoring)
- AI architecture copilot (natural language queries over the graph)
- Domain intelligence (automatic business boundary detection)
- Software Digital Twin (continuously updated live graph)
- React 2D viewer + full 3D universe mode
- Neo4j backend for enterprise-scale repos
- Multi-repository graph merging

---

## License

MIT — free to use, modify, and distribute.

Built by [manish-surya-r](https://github.com/manish-surya-r) · Zealous Engineering
