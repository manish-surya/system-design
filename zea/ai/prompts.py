"""Prompt templates for ZEA AI architecture analysis."""

SYSTEM_PROMPT = """You are a senior software architect with deep expertise in system design, microservices, distributed systems, and cloud-native architecture.

Your job is to analyze a software repository and produce a precise, structured architectural description that will be used to render an interactive 3D system design diagram.

Rules:
- Be concrete and specific. Use actual service names from the codebase.
- Infer capabilities from the code evidence provided.
- Classify every component into a layer: frontend | gateway | service | data | messaging | infrastructure | external
- Classify every connection as: wired (synchronous HTTP/gRPC/function call) OR wireless (async event/queue/pub-sub)
- Return ONLY valid JSON. No markdown, no explanation outside the JSON."""

USER_PROMPT_TEMPLATE = """Analyze this software repository and produce a structured system design description.

=== REPOSITORY INVENTORY ===
Name: {repo_name}
Primary Language: {primary_language}
Languages detected: {languages}
Frameworks detected: {frameworks}
Package managers: {package_managers}
Infrastructure: {infrastructure}
Has tests: {has_tests}
Has CI: {has_ci}
Total files: {total_files}

=== ARCHITECTURE GRAPH (from static analysis) ===
Nodes ({node_count}):
{nodes_summary}

Edges ({edge_count}):
{edges_summary}

=== TASK ===
Return a JSON object with this exact schema:

{{
  "system_description": "One clear sentence describing what this system does",
  "system_type": "monolith | microservices | monorepo | library | cli | data-pipeline | unknown",
  "components": [
    {{
      "node_id": "<matches a node id from the graph above>",
      "display_name": "<human-readable name>",
      "description": "<what this component does, 1-2 sentences>",
      "capabilities": ["<specific capability>", "<specific capability>"],
      "layer": "frontend | gateway | service | data | messaging | infrastructure | external",
      "shape": "cube | cuboid | cylinder | torus | octahedron | sphere | panel",
      "importance": 1-5
    }}
  ],
  "connections": [
    {{
      "source_id": "<node id>",
      "target_id": "<node id>",
      "edge_type": "CALLS | READS | WRITES | PUBLISHES | CONSUMES | DEPENDS_ON",
      "wire_type": "wired | wireless",
      "label": "<short label like 'REST API', 'event', 'SQL query'>"
    }}
  ],
  "domains": [
    {{
      "name": "<domain name, e.g. Commerce, Identity, Billing>",
      "description": "<what business area>",
      "node_ids": ["<node ids that belong to this domain>"]
    }}
  ]
}}

For components, choose shapes based on their type:
- service/backend/monolith → cube or cuboid
- database/storage → cylinder
- queue/message broker → torus
- event → octahedron
- frontend/UI → cuboid (wide, flat)
- gateway/load balancer → cuboid (wide)
- external system → sphere
- infrastructure/cluster → cuboid (tall)

For connections:
- HTTP calls, database queries, function calls → wired
- Events, pub/sub, queues, webhooks → wireless

Include ALL nodes from the graph in components. Add connections that make architectural sense even if not explicitly in the edge list — infer from the codebase context."""
