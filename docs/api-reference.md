# ZEA API Reference

## CLI

### `zea analyze <repo>`
Static repository scan.

```bash
zea analyze /path/to/repo \
  --output .zea \       # output dir (default: .zea)
  --verbose \           # debug logging
  --no-inference        # skip inference layer
```

Outputs: `repository_inventory.json`, `architecture_graph.json`

### `zea ai-analyze <repo>`
Full AI-powered pipeline.

```bash
zea ai-analyze /path/to/repo \
  --output .zea \
  --model claude-opus-4-6 \
  --verbose
```

Requires `ANTHROPIC_API_KEY`. Falls back to static if not set.

Outputs: all of above + `architecture.json`, `architecture.md`, `service-map.json`, `domain-map.json`, `architecture.html`

### `zea visualize <graph.json>`
Render 3D HTML from an existing graph.

```bash
zea visualize .zea/architecture_graph.json \
  --output architecture.html
```

---

## Python API

### Repository Discovery

```python
from zea.discovery.scanner import scan_repository, save_inventory
from zea.core.config import ZEAConfig
from pathlib import Path

config   = ZEAConfig(output_dir=Path(".zea"))
inventory = scan_repository(Path("/path/to/repo"), config)
save_inventory(inventory, config.output_path("repository_inventory.json"))

print(inventory.primary_language)   # "python"
print(inventory.frameworks)         # [FrameworkDetection(framework='fastapi', ...)]
print(inventory.total_files)        # 342
```

### Graph Building

```python
from zea.graph.builder import AKGBuilder
from zea.graph.serializer import save_graph

builder = AKGBuilder(inventory)
akg = builder.build()
save_graph(akg, Path(".zea/architecture_graph.json"))

print(akg.node_count)   # 42
print(akg.edge_count)   # 38
```

### Architecture Inference

```python
from zea.inference.engine import InferenceEngine

engine = InferenceEngine(akg, Path("/path/to/repo"))
akg = engine.run()
# Now akg has services, APIs, databases, events, CALLS edges
```

### AI Analysis

```python
from zea.ai.analyzer import analyze_with_claude, save_analysis
import json

inventory_dict = json.loads(Path(".zea/repository_inventory.json").read_text())
graph_dict     = json.loads(Path(".zea/architecture_graph.json").read_text())

analysis = analyze_with_claude(inventory_dict, graph_dict, model="claude-opus-4-6")
save_analysis(analysis, Path(".zea"))
```

### 3D Visualization

```python
from zea.visualization.threejs_generator import generate_html, generate_html_from_file

# From analysis dict (AI-enriched)
generate_html(analysis, Path(".zea/architecture.html"))

# From graph JSON file (static fallback)
generate_html_from_file(
    Path(".zea/architecture_graph.json"),
    Path(".zea/architecture.html")
)
```

---

## Data Models

### RepositoryInventory

```python
class RepositoryInventory(BaseModel):
    repository_path: str
    repository_name: str
    languages: list[LanguageStats]       # sorted by file_count desc
    primary_language: Language
    frameworks: list[FrameworkDetection]
    package_managers: list[PackageManagerDetection]
    infrastructure: list[InfrastructureDetection]
    documentation: list[DocumentationDetection]
    total_files: int
    total_directories: int
    has_tests: bool
    has_ci: bool
```

### AKGNode

```python
class AKGNode(BaseModel):
    id: str                   # unique, e.g. "svc_order"
    name: str
    type: NodeType            # service|database|queue|event|...
    language: str | None
    framework: str | None
    repository: str | None
    path: str | None          # source path in repo
    metadata: dict[str, Any]
    evidence: EvidenceSet
    tags: list[str]
```

### NodeType enum

`repository | frontend | backend | monolith | gateway | worker | service | microservice | rest_api | graphql_api | grpc_api | webhook | database | cache | queue | topic | event | domain | cluster | namespace | pod | load_balancer | vpc | team | external_system`

### EdgeType enum

`DEPENDS_ON | IMPORTS | REFERENCES | CALLS | INVOKES | CONNECTS_TO | READS | WRITES | OWNS | PUBLISHES | CONSUMES | CONTAINS | BELONGS_TO | OWNED_BY | DEPLOYED_IN`

### Evidence

```python
class Evidence(BaseModel):
    type: EvidenceType        # file_pattern|directory_structure|package_dependency|...
    description: str
    source: str               # file path or pattern
    confidence: float         # 0.0 – 1.0
    details: dict[str, str]
```

---

## Plugin API

```python
from zea.plugins.base import DetectorPlugin
from zea.plugins.registry import registry
from zea.graph.schema import ArchitectureKnowledgeGraph, AKGNode, AKGEdge
from zea.graph.taxonomy import NodeType, EdgeType
from pathlib import Path

class MyDetector(DetectorPlugin):
    name = "my_detector"
    version = "1.0.0"
    description = "Detects custom components"

    def run(self, akg: ArchitectureKnowledgeGraph, repo_path: Path):
        # Scan repo, create nodes/edges, add to akg
        node = AKGNode(id="my_node", name="My Component", type=NodeType.SERVICE)
        akg.nodes.append(node)
        return akg

registry.register(MyDetector())
```
