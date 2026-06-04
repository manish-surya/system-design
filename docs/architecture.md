# ZEA Architecture

## Core Principle

> Never generate outputs without going through the Architecture Knowledge Graph.

```
Repository
→ Discovery Layer
→ Inference Layer
→ Architecture Knowledge Graph  ← central artifact
→ AI Enrichment
→ Visualization / Reports / Slash Commands
```

## Layer Responsibilities

### 1. Discovery (`zea/discovery/`)
Scans the repository. Does NOT infer — only observes.
- `scanner.py` — orchestrates all detectors
- `language_detector.py` — file extension → Language enum
- `framework_detector.py` — package.json, requirements.txt, go.mod, pom.xml
- `package_detector.py` — lock files + manifest files
- `doc_detector.py` — README, OpenAPI, ADRs, architecture docs

Output: `RepositoryInventory` (Pydantic model)

### 2. Graph Schema (`zea/graph/`)
Defines the canonical data model.
- `taxonomy.py` — `NodeType` + `EdgeType` enums (30+ types)
- `schema.py` — `AKGNode`, `AKGEdge`, `ArchitectureKnowledgeGraph`
- `builder.py` — `AKGBuilder`: inventory → NetworkX graph
- `serializer.py` — JSON save/load

### 3. Inference (`zea/inference/`)
Converts code structures into architecture. All inferences cite **evidence** (file path + confidence score).
- `service_detector.py` — monorepo containers, naming conventions, Dockerfile presence
- `api_detector.py` — route decorators (FastAPI/Flask/Express/NestJS/Spring/Gin)
- `database_detector.py` — dependency strings + env vars
- `event_detector.py` — messaging system deps + domain event name patterns
- `dependency_detector.py` — HTTP client calls → inter-service CALLS edges

### 4. AI Analysis (`zea/ai/`)
Optional Claude API enrichment.
- `analyzer.py` — sends inventory + graph to Claude, returns structured analysis
- `prompts.py` — system + user prompt templates
- Falls back to static analysis if `ANTHROPIC_API_KEY` not set

### 5. Visualization (`zea/visualization/`)
- `threejs_generator.py` — generates standalone `architecture.html`
  - Dark ground surface + grid
  - 3D component objects by type (box/cylinder/torus/octahedron/sphere/cone)
  - Wired connections: `TubeGeometry` along bezier curves
  - Wireless connections: dashed `LineDashedMaterial` + torus signal rings
  - HTML overlay labels, click-to-inspect panel, legend with type toggle

### 6. Plugin Architecture (`zea/plugins/`)
```python
class MyDetector(DetectorPlugin):
    name = "my_detector"

    def run(self, akg: ArchitectureKnowledgeGraph, repo_path: Path):
        # add nodes/edges to akg
        return akg

registry.register(MyDetector())
```

## Evidence Model

Every inference must cite evidence:
```python
Evidence(
    type=EvidenceType.FILE_PATTERN,
    description="Found 'psycopg2' in requirements.txt",
    source="requirements.txt",
    confidence=0.9,
)
```

This ensures every architectural conclusion is explainable.

## Graph Schema

```
Node {
  id: str              # unique, e.g. "svc_order"
  name: str            # human-readable
  type: NodeType       # service | database | queue | event | ...
  language: str?
  framework: str?
  repository: str?
  path: str?           # source path in repo
  metadata: dict
  evidence: EvidenceSet
}

Edge {
  source_id: str
  target_id: str
  type: EdgeType       # CALLS | READS | WRITES | PUBLISHES | ...
  metadata: dict
  evidence: EvidenceSet
}
```
