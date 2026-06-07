# Getting Started with ZEA

## Installation

```bash
pip install system-design
```

For AI-powered analysis:
```bash
pip install system-design anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

## Your First Analysis

```bash
# 1. Navigate to any repository
cd /path/to/your/project

# 2. Run ZEA
system-design analyze .

# 3. View results
cat .zea/repository_inventory.json
cat .zea/architecture_graph.json

# 4. Generate 3D visualization
system-design visualize .zea/architecture_graph.json
open .zea/architecture.html
```

## With AI (Claude)

```bash
export ANTHROPIC_API_KEY=your_key
system-design ai-analyze .
open .zea/architecture.html
```

This runs the full pipeline:
1. Static scan → detects languages, frameworks, services, APIs, databases, events
2. Claude API → enriches with descriptions, capabilities, domains
3. 3D render → interactive system design in your browser

## Using the 3D Viewer

| Control | Action |
|---------|--------|
| Left-drag | Rotate camera |
| Right-drag | Pan |
| Scroll | Zoom in/out |
| Click component | Open detail panel |
| Legend items | Toggle visibility by type |

## Using with Claude Code

Copy the skill file into your project:

```bash
mkdir -p .claude/skills/system-design
cp /path/to/zea/skills/claude-code/SKILL.md .claude/skills/system-design/SKILL.md
```

Then in Claude Code, type:
- `/system-design` — full 3D architecture
- `/service-map` — service dependencies
- `/data-flow` — request flow trace
- `/impact-analysis OrderService` — blast radius analysis
