# ZEA — Architecture Intelligence Skill for Claude Code

ZEA transforms any repository into a living 3D architecture graph and system design visualization.
Claude uses ZEA to answer architectural questions, generate system designs, and understand codebases at the service/domain level — not just file-by-file.

---

## Installation

```bash
pip install zea
# For AI-powered analysis (recommended):
pip install zea anthropic
export ANTHROPIC_API_KEY=your_key_here
```

---

## Slash Commands

### `/system-design`
Generate a complete 3D interactive system design for the current repository.

**What Claude should do:**
```bash
zea ai-analyze . --output .zea
```
Then open `.zea/architecture.html`.

Read `.zea/architecture.json` and tell the user:
- What type of system this is (microservices, monolith, etc.)
- The main services/components found
- How they connect
- Any domains identified

**Outputs generated:**
| File | Description |
|------|-------------|
| `.zea/repository_inventory.json` | Languages, frameworks, package managers |
| `.zea/architecture_graph.json` | Knowledge graph (nodes + edges) |
| `.zea/architecture.json` | AI-enriched analysis |
| `.zea/architecture.md` | Human-readable system design doc |
| `.zea/service-map.json` | Service dependency map |
| `.zea/domain-map.json` | Business domain map |
| `.zea/architecture.html` | **3D interactive system design** |

---

### `/service-map`
Show all services and their dependencies.

```bash
zea analyze . --output .zea
```
Read `.zea/architecture_graph.json`. Filter nodes by type: service, backend, frontend, gateway.
Report names, languages, frameworks, and connections.

---

### `/data-flow`
Trace data flow: User → API → Service → Database.

```bash
zea analyze . --output .zea
```
Read `.zea/architecture_graph.json`. Follow CALLS edges from frontend → gateway → service → database.
Present as a numbered flow diagram.

---

### `/domain-map`
Identify business domains.

```bash
zea ai-analyze . --output .zea
```
Read `.zea/domain-map.json`. Group services by domain. Explain each domain's responsibility.

---

### `/impact-analysis <component>`
What breaks if I change this component?

```bash
zea analyze . --output .zea
```
Read `.zea/architecture_graph.json`. Find all nodes with CALLS/READS/DEPENDS_ON/CONSUMES edges TO the named component. List by risk level.

---

### `/architecture-review`
Review for coupling issues and anti-patterns.

```bash
zea ai-analyze . --output .zea
```
Analyze `.zea/architecture.json` for: high coupling, missing boundaries, circular dependencies, god services.

---

## Node Types

| Type | Shape in 3D | Color |
|------|-------------|-------|
| frontend | Flat wide box | Teal |
| gateway | Wide box | Dark purple |
| service / backend | Cube | Blue |
| database | Cylinder | Green |
| cache | Small cylinder | Light green |
| queue | Torus ring | Orange |
| event | Octahedron | Red-orange |
| external_system | Sphere | Red |
| cluster / infra | Tall box | Gray |

## Edge Types

| Type | Wire | Meaning |
|------|------|---------|
| CALLS | Wired (tube) | Sync HTTP/gRPC call |
| READS | Wired (tube) | Database read |
| WRITES | Wired (tube) | Database write |
| DEPENDS_ON | Wired (tube) | Package dependency |
| PUBLISHES | Wireless (dashed arc) | Publishes event |
| CONSUMES | Wireless (dashed arc) | Consumes event |

---

## Questions Claude Can Answer After Running ZEA

- "What services exist in this repo?"
- "What databases does the Order Service use?"
- "What events are published and by whom?"
- "What breaks if I change the Payment Service?"
- "Which domain owns checkout?"
- "Are there circular dependencies?"
- "What is the critical purchase path?"
- "Which services are most coupled?"
- "Where is the API gateway?"

---

## Static Mode (no API key)

```bash
zea analyze . --output .zea
zea visualize .zea/architecture_graph.json --output .zea/architecture.html
```
