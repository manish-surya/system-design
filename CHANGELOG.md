# Changelog

## [0.1.0] — 2026-06-03

### Added
- **Milestone 0**: Typer-based CLI — `system-design analyze`, `system-design ai-analyze`, `system-design visualize`, `system-design version`
- **Milestone 1**: Repository Discovery — language, framework, package manager, infrastructure, documentation detection
- **Milestone 2**: Architecture Knowledge Graph — NodeType/EdgeType taxonomy, Pydantic schema, NetworkX builder, JSON serializer
- **Milestone 3**: Architecture Inference — service detector, API route detector, database detector, event/messaging detector, inter-service CALLS edge detector
- **Milestone 3.5**: AI Architecture Analysis — Claude API integration with structured output (descriptions, capabilities, domains); static fallback when no API key
- **Milestone 6**: 3D System Design Viewer — Three.js r128, dark surface + grid, 3D objects by type (box/cylinder/torus/octahedron/sphere/cone), wired tube connections, wireless dashed arc connections, click-to-inspect panel, layer legend, search
- **Claude Code Skill** — `/system-design`, `/service-map`, `/data-flow`, `/domain-map`, `/impact-analysis`, `/architecture-review`
- **Codex + Gemini CLI plugins** — plugin.json and plugin.yaml manifests
- **Benchmark suite** — smoke tests + precision/recall metrics for language/framework/node detection
- **Open source packaging** — MIT license, GitHub Actions CI, PyPI classifiers, CONTRIBUTING.md, Makefile

### Benchmark Results
- fastapi: 100% · 109 nodes
- express: 100% · 40 nodes  
- nestjs: 100% · 122 nodes · 163 edges
