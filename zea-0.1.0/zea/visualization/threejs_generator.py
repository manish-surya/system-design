"""
threejs_generator.py
====================
Generates a self-contained architecture.html file that renders the
Architecture Knowledge Graph as an interactive 3D scene using Three.js r128.

Usage (programmatic):
    from zea.visualization.threejs_generator import generate_html
    generate_html(graph_data, output_path)

Usage (CLI):
    zea visualize examples/architecture_graph.json --output architecture.html
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union


# ---------------------------------------------------------------------------
# Color palette — one hex color per node type
# ---------------------------------------------------------------------------
NODE_COLORS: dict[str, str] = {
    "repository":      "#ffffff",
    "frontend":        "#00e5ff",   # cyan
    "backend":         "#2979ff",   # blue
    "monolith":        "#3d5afe",   # indigo-blue
    "gateway":         "#651fff",   # deep-purple
    "worker":          "#d500f9",   # purple/magenta
    "service":         "#2979ff",   # blue (same family as backend)
    "microservice":    "#1e88e5",
    "rest_api":        "#aa00ff",   # purple
    "graphql_api":     "#e040fb",   # pink-purple
    "grpc_api":        "#7c4dff",   # violet
    "webhook":         "#b388ff",   # light-purple
    "database":        "#00e676",   # green
    "cache":           "#69f0ae",   # light-green
    "queue":           "#ff9100",   # amber/orange
    "topic":           "#ffab40",   # light-orange
    "event":           "#ff6d00",   # deep-orange
    "domain":          "#f50057",   # pink-red
    "cluster":         "#546e7a",   # blue-grey
    "namespace":       "#607d8b",   # blue-grey lighter
    "pod":             "#78909c",   # even lighter
    "load_balancer":   "#90a4ae",
    "team":            "#ffee58",   # yellow
    "external_system": "#ff5252",   # red
}
DEFAULT_COLOR = "#aaaaaa"


def _node_color(node_type: str) -> str:
    return NODE_COLORS.get(node_type.lower(), DEFAULT_COLOR)


def _build_legend_entries() -> list[dict]:
    """Return a deduplicated, sorted list of {type, color} for the legend."""
    seen: dict[str, str] = {}
    for t, c in NODE_COLORS.items():
        # Group similar types under a display label
        seen[t] = c
    return [{"type": t, "color": c} for t, c in sorted(seen.items())]


# ---------------------------------------------------------------------------
# HTML template — parametrised at render time
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ZEA — {repo_name} Architecture</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    background: #0a0a1a;
    color: #e0e0ff;
    font-family: 'Segoe UI', system-ui, sans-serif;
    overflow: hidden;
  }}

  /* ── Header ── */
  #header {{
    position: fixed; top: 0; left: 0; right: 0;
    padding: 12px 24px;
    background: rgba(10,10,30,0.85);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid rgba(100,100,255,0.2);
    display: flex; align-items: center; gap: 24px;
    z-index: 20;
  }}
  #header h1 {{ font-size: 1.1rem; letter-spacing: 0.08em; color: #a0a0ff; }}
  #header h1 span {{ color: #fff; }}
  .stat {{
    font-size: 0.78rem;
    color: #7070aa;
    border: 1px solid rgba(100,100,255,0.2);
    border-radius: 4px;
    padding: 3px 10px;
  }}
  .stat b {{ color: #c0c0ff; }}

  /* ── Canvas ── */
  #c {{ display:block; width:100vw; height:100vh; }}

  /* ── Tooltip ── */
  #tooltip {{
    position: fixed;
    pointer-events: none;
    background: rgba(10,10,30,0.92);
    border: 1px solid rgba(120,120,255,0.4);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 0.82rem;
    line-height: 1.5;
    display: none;
    z-index: 30;
    max-width: 220px;
  }}
  #tooltip .tt-name {{ font-weight: 700; color: #fff; }}
  #tooltip .tt-type {{ color: #8888cc; font-size: 0.73rem; text-transform: uppercase; letter-spacing: 0.06em; }}

  /* ── Legend ── */
  #legend {{
    position: fixed; bottom: 20px; right: 20px;
    background: rgba(10,10,30,0.88);
    backdrop-filter: blur(6px);
    border: 1px solid rgba(100,100,255,0.2);
    border-radius: 10px;
    padding: 14px 18px;
    max-height: 70vh;
    overflow-y: auto;
    z-index: 20;
    font-size: 0.73rem;
  }}
  #legend h3 {{
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6666aa;
    margin-bottom: 10px;
  }}
  .legend-item {{
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 6px; white-space: nowrap;
  }}
  .legend-dot {{
    width: 10px; height: 10px; border-radius: 50%;
    flex-shrink: 0;
  }}
  .legend-label {{ color: #b0b0dd; }}

  /* ── Controls hint ── */
  #controls-hint {{
    position: fixed; bottom: 20px; left: 20px;
    font-size: 0.68rem;
    color: #444466;
    line-height: 1.7;
    z-index: 20;
  }}
</style>
</head>
<body>

<!-- Header -->
<div id="header">
  <h1>ZEA &mdash; <span>{repo_name}</span></h1>
  <div class="stat">Nodes <b>{node_count}</b></div>
  <div class="stat">Edges <b>{edge_count}</b></div>
</div>

<!-- Three.js canvas -->
<canvas id="c"></canvas>

<!-- Hover tooltip -->
<div id="tooltip">
  <div class="tt-name" id="tt-name"></div>
  <div class="tt-type" id="tt-type"></div>
</div>

<!-- Legend -->
<div id="legend">
  <h3>Node Types</h3>
{legend_html}
</div>

<!-- Controls hint -->
<div id="controls-hint">
  Drag &nbsp; Rotate<br>
  Scroll &nbsp; Zoom<br>
  Hover &nbsp; Inspect
</div>

<!-- Three.js r128 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

<script>
// ============================================================
//  GRAPH DATA  (injected by Python)
// ============================================================
const GRAPH = {graph_json};

// ============================================================
//  NODE COLOR MAP
// ============================================================
const NODE_COLORS = {node_colors_json};
function nodeColor(type) {{
  return NODE_COLORS[type] || 0xaaaaaa;
}}

// ============================================================
//  SCENE SETUP
// ============================================================
const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a1a);
scene.fog = new THREE.FogExp2(0x0a0a1a, 0.003);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 5000);
camera.position.set(0, 0, 300);

// Ambient + point lights
scene.add(new THREE.AmbientLight(0x223366, 1.2));
const pLight1 = new THREE.PointLight(0x4466ff, 2, 800);
pLight1.position.set(200, 200, 200);
scene.add(pLight1);
const pLight2 = new THREE.PointLight(0xff6644, 1.5, 600);
pLight2.position.set(-200, -100, -150);
scene.add(pLight2);

// ============================================================
//  ORBIT CONTROLS  (manual implementation)
// ============================================================
const orbit = {{
  theta: 0, phi: Math.PI / 2,
  radius: 300,
  dragging: false,
  lastX: 0, lastY: 0,
}};

canvas.addEventListener('mousedown', (e) => {{
  orbit.dragging = true;
  orbit.lastX = e.clientX;
  orbit.lastY = e.clientY;
}});
window.addEventListener('mouseup', () => {{ orbit.dragging = false; }});
window.addEventListener('mousemove', (e) => {{
  if (!orbit.dragging) return;
  const dx = e.clientX - orbit.lastX;
  const dy = e.clientY - orbit.lastY;
  orbit.lastX = e.clientX;
  orbit.lastY = e.clientY;
  orbit.theta -= dx * 0.005;
  orbit.phi   = Math.max(0.1, Math.min(Math.PI - 0.1, orbit.phi - dy * 0.005));
  updateCamera();
}});
canvas.addEventListener('wheel', (e) => {{
  orbit.radius = Math.max(50, Math.min(2000, orbit.radius + e.deltaY * 0.3));
  updateCamera();
}}, {{ passive: true }});

function updateCamera() {{
  camera.position.x = orbit.radius * Math.sin(orbit.phi) * Math.sin(orbit.theta);
  camera.position.y = orbit.radius * Math.cos(orbit.phi);
  camera.position.z = orbit.radius * Math.sin(orbit.phi) * Math.cos(orbit.theta);
  camera.lookAt(0, 0, 0);
}}
updateCamera();

// ============================================================
//  NODE PLACEMENT — Fibonacci sphere layout (initial)
// ============================================================
const N = GRAPH.nodes.length;
const SPHERE_RADIUS = Math.max(80, N * 6);

function fibonacciSphere(i, n, r) {{
  const golden = Math.PI * (3 - Math.sqrt(5));
  const y = 1 - (i / (n - 1 || 1)) * 2;
  const rad = Math.sqrt(1 - y * y) * r;
  const theta = golden * i;
  return {{ x: Math.cos(theta) * rad, y: y * r, z: Math.sin(theta) * rad }};
}}

// Physics state
const positions = GRAPH.nodes.map((_, i) => {{
  const p = N > 1 ? fibonacciSphere(i, N, SPHERE_RADIUS) : {{ x:0, y:0, z:0 }};
  return {{ x: p.x, y: p.y, z: p.z, vx: 0, vy: 0, vz: 0 }};
}});

// Index map  id → array index
const nodeIndex = {{}};
GRAPH.nodes.forEach((n, i) => {{ nodeIndex[n.id] = i; }});

// ============================================================
//  BUILD THREE.JS OBJECTS
// ============================================================
const NODE_RADIUS = 5;

// Geometry shared by all spheres
const geo = new THREE.SphereGeometry(NODE_RADIUS, 24, 24);

// One mesh per node
const meshes = GRAPH.nodes.map((node) => {{
  const hex = parseInt((nodeColor(node.type) || '#aaaaaa').replace('#',''), 16);
  const mat = new THREE.MeshPhongMaterial({{
    color: hex,
    emissive: hex,
    emissiveIntensity: 0.45,
    shininess: 120,
  }});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.userData = {{ id: node.id, name: node.name, type: node.type }};
  scene.add(mesh);
  return mesh;
}});

// Edges as LineSegments
const edgePositions = [];
GRAPH.edges.forEach((edge) => {{
  const si = nodeIndex[edge.source_id];
  const ti = nodeIndex[edge.target_id];
  if (si === undefined || ti === undefined) return;
  edgePositions.push(si, ti);
}});

const lineGeo = new THREE.BufferGeometry();
const linePositionBuffer = new Float32Array(edgePositions.length * 3); // placeholder
lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositionBuffer, 3));
const lineMat = new THREE.LineBasicMaterial({{ color: 0x334488, transparent: true, opacity: 0.55 }});
const lineSegments = new THREE.LineSegments(lineGeo, lineMat);
scene.add(lineSegments);

// ============================================================
//  TEXT LABELS  (canvas sprite, one per node)
// ============================================================
function makeLabel(text) {{
  const canvas2 = document.createElement('canvas');
  canvas2.width = 256; canvas2.height = 64;
  const ctx = canvas2.getContext('2d');
  ctx.font = 'bold 22px Segoe UI, sans-serif';
  ctx.fillStyle = 'rgba(0,0,0,0)';
  ctx.fillRect(0,0,256,64);
  ctx.fillStyle = '#e0e0ff';
  ctx.shadowColor = '#0a0a1a';
  ctx.shadowBlur = 6;
  ctx.textAlign = 'center';
  ctx.fillText(text, 128, 42);
  const tex = new THREE.CanvasTexture(canvas2);
  const spriteMat = new THREE.SpriteMaterial({{ map: tex, transparent: true, depthWrite: false }});
  const sprite = new THREE.Sprite(spriteMat);
  sprite.scale.set(28, 7, 1);
  return sprite;
}}

const labels = GRAPH.nodes.map((node) => {{
  const sp = makeLabel(node.name);
  scene.add(sp);
  return sp;
}});

// ============================================================
//  FORCE SIMULATION
// ============================================================
const REPULSION  = 800;     // repulsion constant (node-node)
const SPRING_K   = 0.018;   // spring stiffness
const REST_LEN   = SPHERE_RADIUS * 0.55;  // ideal edge length
const DAMPING    = 0.82;    // velocity damping per tick
const CENTER_K   = 0.004;   // gentle pull to origin

function stepForce() {{
  const n = positions.length;
  const fx = new Float64Array(n);
  const fy = new Float64Array(n);
  const fz = new Float64Array(n);

  // Repulsion — O(n²) but fine for typical graph sizes
  for (let i = 0; i < n; i++) {{
    for (let j = i+1; j < n; j++) {{
      let dx = positions[j].x - positions[i].x;
      let dy = positions[j].y - positions[i].y;
      let dz = positions[j].z - positions[i].z;
      const dist2 = dx*dx + dy*dy + dz*dz + 1e-4;
      const dist  = Math.sqrt(dist2);
      const force = REPULSION / dist2;
      const ux = dx/dist, uy = dy/dist, uz = dz/dist;
      fx[i] -= ux*force; fy[i] -= uy*force; fz[i] -= uz*force;
      fx[j] += ux*force; fy[j] += uy*force; fz[j] += uz*force;
    }}
  }}

  // Spring attraction along edges
  GRAPH.edges.forEach((edge) => {{
    const si = nodeIndex[edge.source_id];
    const ti = nodeIndex[edge.target_id];
    if (si === undefined || ti === undefined) return;
    const dx = positions[ti].x - positions[si].x;
    const dy = positions[ti].y - positions[si].y;
    const dz = positions[ti].z - positions[si].z;
    const dist = Math.sqrt(dx*dx + dy*dy + dz*dz) + 1e-4;
    const force = SPRING_K * (dist - REST_LEN);
    const ux = dx/dist, uy = dy/dist, uz = dz/dist;
    fx[si] += ux*force; fy[si] += uy*force; fz[si] += uz*force;
    fx[ti] -= ux*force; fy[ti] -= uy*force; fz[ti] -= uz*force;
  }});

  // Integrate
  for (let i = 0; i < n; i++) {{
    // Centering force
    fx[i] -= positions[i].x * CENTER_K;
    fy[i] -= positions[i].y * CENTER_K;
    fz[i] -= positions[i].z * CENTER_K;

    positions[i].vx = (positions[i].vx + fx[i]) * DAMPING;
    positions[i].vy = (positions[i].vy + fy[i]) * DAMPING;
    positions[i].vz = (positions[i].vz + fz[i]) * DAMPING;

    positions[i].x += positions[i].vx;
    positions[i].y += positions[i].vy;
    positions[i].z += positions[i].vz;
  }}
}}

// ============================================================
//  RAYCASTING / HOVER
// ============================================================
const raycaster  = new THREE.Raycaster();
const mouse      = new THREE.Vector2(-9999, -9999);
const tooltip    = document.getElementById('tooltip');
const ttName     = document.getElementById('tt-name');
const ttType     = document.getElementById('tt-type');

window.addEventListener('mousemove', (e) => {{
  mouse.x =  (e.clientX / window.innerWidth)  * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  tooltip.style.left = (e.clientX + 16) + 'px';
  tooltip.style.top  = (e.clientY - 10) + 'px';
}});

let forceSteps = 0;
const MAX_FORCE_STEPS = 300; // run simulation for ~300 frames then let it settle

// ============================================================
//  MAIN ANIMATION LOOP
// ============================================================
let time = 0;

function animate() {{
  requestAnimationFrame(animate);
  time += 0.016;

  // Run force simulation for the first N frames, then keep slow ticking
  if (forceSteps < MAX_FORCE_STEPS) {{
    stepForce();
    forceSteps++;
  }} else if (forceSteps % 6 === 0) {{
    stepForce();  // gentle continuous settling
  }}
  forceSteps++;

  // Sync mesh positions + gentle bob
  for (let i = 0; i < meshes.length; i++) {{
    const p = positions[i];
    const bob = Math.sin(time * 0.7 + i * 1.3) * 1.2;
    meshes[i].position.set(p.x, p.y + bob, p.z);
    labels[i].position.set(p.x, p.y + bob + NODE_RADIUS * 1.7, p.z);
  }}

  // Update edge line geometry
  const posAttr = lineGeo.attributes.position;
  for (let e = 0; e < edgePositions.length; e += 2) {{
    const si = edgePositions[e];
    const ti = edgePositions[e+1];
    const sp = meshes[si].position;
    const tp = meshes[ti].position;
    const idx = e * 3;
    posAttr.array[idx]   = sp.x; posAttr.array[idx+1] = sp.y; posAttr.array[idx+2] = sp.z;
    posAttr.array[idx+3] = tp.x; posAttr.array[idx+4] = tp.y; posAttr.array[idx+5] = tp.z;
  }}
  posAttr.needsUpdate = true;

  // Raycasting for hover
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(meshes);
  if (hits.length > 0) {{
    const ud = hits[0].object.userData;
    ttName.textContent = ud.name;
    ttType.textContent = ud.type;
    tooltip.style.display = 'block';
  }} else {{
    tooltip.style.display = 'none';
  }}

  renderer.render(scene, camera);
}}

// ============================================================
//  RESIZE HANDLER
// ============================================================
window.addEventListener('resize', () => {{
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}});

animate();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_html(graph_data: dict, output_path: Union[str, Path]) -> Path:
    """
    Generate a self-contained 3D architecture visualisation HTML file.

    Parameters
    ----------
    graph_data:
        Parsed architecture_graph.json as a Python dict.
    output_path:
        Destination path for the .html file.

    Returns
    -------
    Path
        Resolved absolute path of the written file.
    """
    output_path = Path(output_path).resolve()

    repo_name   = graph_data.get("repository_name", "Architecture")
    nodes       = graph_data.get("nodes", [])
    edges       = graph_data.get("edges", [])

    # Build legend HTML
    present_types = sorted({n.get("type", "unknown") for n in nodes})
    legend_rows = []
    for t in present_types:
        color = _node_color(t)
        legend_rows.append(
            f'  <div class="legend-item">'
            f'<div class="legend-dot" style="background:{color};'
            f' box-shadow:0 0 6px {color};"></div>'
            f'<span class="legend-label">{t}</span></div>'
        )
    legend_html = "\n".join(legend_rows)

    # Build JS color map (hex strings)
    node_colors_js = {t: _node_color(t) for t in NODE_COLORS}
    # Also include any types in the graph not in our palette
    for n in nodes:
        t = n.get("type", "unknown")
        if t not in node_colors_js:
            node_colors_js[t] = DEFAULT_COLOR

    # Convert colors to JS-friendly format (keep as hex strings; JS parses them)
    node_colors_json = json.dumps(node_colors_js, indent=2)

    # Minimal graph JSON — only what the JS needs
    graph_js = {
        "nodes": [
            {
                "id":   n.get("id", f"node_{i}"),
                "name": n.get("name", n.get("id", f"node_{i}")),
                "type": n.get("type", "unknown"),
            }
            for i, n in enumerate(nodes)
        ],
        "edges": [
            {
                "source_id": e.get("source_id", ""),
                "target_id": e.get("target_id", ""),
                "type":      e.get("type", ""),
            }
            for e in edges
            if e.get("source_id") and e.get("target_id")
        ],
    }
    graph_json = json.dumps(graph_js, indent=2)

    html = _HTML_TEMPLATE.format(
        repo_name        = repo_name,
        node_count       = len(nodes),
        edge_count       = len(edges),
        legend_html      = legend_html,
        graph_json       = graph_json,
        node_colors_json = node_colors_json,
    )

    output_path.write_text(html, encoding="utf-8")
    return output_path


def generate_html_from_file(
    graph_path: Union[str, Path],
    output_path: Union[str, Path],
) -> Path:
    """
    Convenience wrapper: read architecture_graph.json then call generate_html.

    Parameters
    ----------
    graph_path:
        Path to architecture_graph.json.
    output_path:
        Destination path for the .html file.
    """
    graph_path = Path(graph_path).resolve()
    with graph_path.open(encoding="utf-8") as f:
        graph_data = json.load(f)
    return generate_html(graph_data, output_path)
