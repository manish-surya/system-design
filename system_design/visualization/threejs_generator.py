"""
threejs_generator.py
====================
Generates a self-contained architecture.html — a 3D system design scene.

Scene elements:
  - Dark surface with grid lines (the "deployment environment")
  - 3D component objects ON the surface: cubes, cuboids, cylinders,
    torus rings, octahedra, panels — shape determined by component type
  - Wired connections: tube geometry along bezier curves (sync calls)
  - Wireless connections: dashed arcs (async events, pub-sub)
  - Canvas-sprite labels above each component
  - Click-to-inspect panel showing description + capabilities
  - Orbit camera (drag=rotate, scroll=zoom, right-drag=pan)

Data flow:
  analysis dict (from ai/analyzer.py or static fallback)
  → generate_html(analysis, output_path)
  → standalone architecture.html
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Union

# ── Component shape + color catalogue ─────────────────────────────────────────
# Every node type maps to a shape primitive and a color.
# Shapes: box | cylinder | torus | octahedron | sphere | cone | ring
# These are all standard Three.js BufferGeometry constructors.

COMPONENT_DEFS: dict[str, dict] = {
    # ── Application layer ──────────────────────────────────────────────────
    "repository":       {"shape": "box",       "w":60,"h":60,"d":60,  "color":"#1a237e","emissive":"#0a1040","importance":5},
    "frontend":         {"shape": "box",       "w":90,"h":12,"d":55,  "color":"#006064","emissive":"#00292c","importance":4},
    "backend":          {"shape": "box",       "w":55,"h":55,"d":55,  "color":"#1565c0","emissive":"#062a60","importance":4},
    "monolith":         {"shape": "box",       "w":70,"h":70,"d":70,  "color":"#283593","emissive":"#0d1840","importance":5},
    "gateway":          {"shape": "box",       "w":80,"h":18,"d":50,  "color":"#4a148c","emissive":"#1a0530","importance":4},
    "worker":           {"shape": "box",       "w":45,"h":45,"d":45,  "color":"#880e4f","emissive":"#300520","importance":3},
    # ── Service layer ──────────────────────────────────────────────────────
    "service":          {"shape": "box",       "w":55,"h":55,"d":55,  "color":"#0d47a1","emissive":"#041a40","importance":4},
    "microservice":     {"shape": "box",       "w":45,"h":45,"d":45,  "color":"#1565c0","emissive":"#062a60","importance":3},
    # ── API layer ─────────────────────────────────────────────────────────
    "rest_api":         {"shape": "box",       "w":38,"h":8,"d":22,   "color":"#6a1b9a","emissive":"#240838","importance":2},
    "graphql_api":      {"shape": "box",       "w":38,"h":8,"d":22,   "color":"#7b1fa2","emissive":"#280a3a","importance":2},
    "grpc_api":         {"shape": "box",       "w":38,"h":8,"d":22,   "color":"#8e24aa","emissive":"#2c0a36","importance":2},
    "webhook":          {"shape": "box",       "w":30,"h":8,"d":18,   "color":"#9c27b0","emissive":"#300838","importance":2},
    # ── Data layer ────────────────────────────────────────────────────────
    "database":         {"shape": "cylinder",  "rt":22,"rb":22,"h":38,"segs":16,"color":"#1b5e20","emissive":"#081808","importance":4},
    "cache":            {"shape": "cylinder",  "rt":16,"rb":16,"h":24,"segs":16,"color":"#33691e","emissive":"#0a1a08","importance":3},
    # ── Messaging layer ───────────────────────────────────────────────────
    "queue":            {"shape": "torus",     "r":22,"tube":7,"segs":8,"tsegs":16,"color":"#e65100","emissive":"#4a1800","importance":3},
    "topic":            {"shape": "torus",     "r":18,"tube":5,"segs":8,"tsegs":16,"color":"#ef6c00","emissive":"#4a2000","importance":3},
    "event":            {"shape": "octahedron","r":22,                  "color":"#bf360c","emissive":"#3a0a04","importance":2},
    # ── Domain ────────────────────────────────────────────────────────────
    "domain":           {"shape": "box",       "w":100,"h":6,"d":80,  "color":"#311b92","emissive":"#0d0730","importance":5},
    # ── Infrastructure ────────────────────────────────────────────────────
    "cluster":          {"shape": "box",       "w":45,"h":90,"d":45,  "color":"#37474f","emissive":"#10181c","importance":4},
    "namespace":        {"shape": "box",       "w":35,"h":60,"d":35,  "color":"#455a64","emissive":"#121e22","importance":3},
    "pod":              {"shape": "box",       "w":25,"h":30,"d":25,  "color":"#546e7a","emissive":"#141e22","importance":2},
    "load_balancer":    {"shape": "cylinder",  "rt":28,"rb":28,"h":12,"segs":6, "color":"#00838f","emissive":"#002a30","importance":3},
    "vpc":              {"shape": "box",       "w":80,"h":8,"d":60,   "color":"#004d40","emissive":"#001810","importance":3},
    # ── External + other ──────────────────────────────────────────────────
    "external_system":  {"shape": "sphere",    "r":26,"wsegs":10,"hsegs":8,"color":"#b71c1c","emissive":"#3a0808","importance":3},
    "team":             {"shape": "cone",      "rb":22,"h":40,"segs":8,"color":"#f57f17","emissive":"#5a2c00","importance":2},
}

DEFAULT_DEF = {"shape":"box","w":45,"h":45,"d":45,"color":"#546e7a","emissive":"#141e22","importance":2}

# Edge → wired or wireless
WIRELESS_EDGE_TYPES = {"PUBLISHES","CONSUMES","INVOKES","CONNECTS_TO"}

EDGE_COLORS: dict[str, str] = {
    "CALLS":       "#2196f3",
    "DEPENDS_ON":  "#9c27b0",
    "READS":       "#4caf50",
    "WRITES":      "#ff9800",
    "OWNS":        "#f06292",
    "PUBLISHES":   "#ff5722",
    "CONSUMES":    "#ffc107",
    "CONTAINS":    "#607d8b",
    "BELONGS_TO":  "#607d8b",
    "DEPLOYED_IN": "#78909c",
    "IMPORTS":     "#90a4ae",
    "REFERENCES":  "#90a4ae",
    "INVOKES":     "#42a5f5",
    "CONNECTS_TO": "#80cbc4",
}
DEFAULT_EDGE_COLOR = "#78909c"


def _def(node_type: str) -> dict:
    return COMPONENT_DEFS.get(node_type.lower(), DEFAULT_DEF)


def _edge_color(edge_type: str) -> str:
    return EDGE_COLORS.get(edge_type.upper(), DEFAULT_EDGE_COLOR)


def _is_wireless(edge_type: str) -> bool:
    return edge_type.upper() in WIRELESS_EDGE_TYPES


# ── Layout: layer → zone positions ────────────────────────────────────────────
LAYER_ZONES: dict[str, tuple[float, float]] = {
    # (z_center, x_spread_multiplier)
    "frontend":      (-500, 1.0),
    "gateway":       (-300, 1.0),
    "service":       (   0, 1.2),
    "data":          ( 350, 1.0),
    "messaging":     ( 550, 1.2),
    "infrastructure":( 750, 0.8),
    "external":      (-650, 0.8),
}

# map node type → default layer (for static/non-AI path)
TYPE_TO_LAYER: dict[str, str] = {
    "frontend":"frontend","backend":"service","monolith":"service",
    "gateway":"gateway","worker":"service","service":"service",
    "microservice":"service","rest_api":"gateway","graphql_api":"gateway",
    "grpc_api":"gateway","webhook":"gateway","database":"data","cache":"data",
    "queue":"messaging","topic":"messaging","event":"messaging",
    "domain":"service","cluster":"infrastructure","namespace":"infrastructure",
    "pod":"infrastructure","load_balancer":"gateway","vpc":"infrastructure",
    "external_system":"external","team":"external","repository":"service",
}


def _compute_layout(components: list[dict]) -> dict[str, tuple[float, float]]:
    """
    Return {node_id: (x, z)} positions on the ground plane.
    Groups by layer, then spreads within each zone.
    """
    from collections import defaultdict

    # group by layer
    by_layer: dict[str, list[str]] = defaultdict(list)
    for c in components:
        layer = c.get("layer", TYPE_TO_LAYER.get(c.get("shape_hint",""), "service"))
        by_layer[layer].append(c["node_id"])

    positions: dict[str, tuple[float, float]] = {}
    SPACING = 170  # horizontal spacing between nodes in a layer

    for layer, node_ids in by_layer.items():
        z_center, _ = LAYER_ZONES.get(layer, (0, 1.0))
        n = len(node_ids)
        total_width = (n - 1) * SPACING
        for i, nid in enumerate(node_ids):
            x = -total_width / 2 + i * SPACING
            # Small z-jitter to avoid z-fighting in same layer
            z = z_center + (i % 3 - 1) * 30
            positions[nid] = (x, z)

    return positions


# ── HTML template (using __TOKEN__ replacement, not str.format) ────────────────
_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>system-design | Architecture Intelligence — __REPO_NAME__</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#090912; font-family:'Segoe UI',system-ui,sans-serif; overflow:hidden; color:#e0e0ff; }

/* canvas */
#c { position:fixed; inset:0; width:100%; height:100%; display:block; }

/* labels layer */
#labels { position:fixed; inset:0; pointer-events:none; z-index:10; }
.lbl {
  position:absolute;
  transform:translate(-50%,0);
  font-size:.62rem; font-weight:700;
  color:#e0e8ff;
  text-shadow:0 0 8px rgba(0,0,80,.9), 0 1px 3px #000;
  pointer-events:none; white-space:nowrap;
  letter-spacing:.04em;
}

/* header */
#hdr {
  position:fixed; top:0; left:0; right:0; z-index:30;
  height:48px; padding:0 20px;
  background:rgba(8,8,20,.88); backdrop-filter:blur(10px);
  border-bottom:1px solid rgba(80,80,180,.25);
  display:flex; align-items:center; gap:16px;
  box-shadow:0 2px 20px rgba(0,0,0,.5);
}
#hdr .logo { font-size:.9rem; font-weight:800; color:#4488ff; letter-spacing:.1em; }
#hdr .desc { font-size:.75rem; color:#8888bb; flex:1; }
.pill {
  background:rgba(30,30,80,.7); border:1px solid rgba(80,80,200,.3);
  border-radius:20px; padding:3px 12px; font-size:.7rem; color:#8899cc;
}
.pill b { color:#99bbff; }

/* detail panel */
#panel {
  position:fixed; right:0; top:48px; bottom:0; z-index:25; width:300px;
  background:rgba(8,8,20,.95); border-left:1px solid rgba(60,60,160,.3);
  box-shadow:-4px 0 30px rgba(0,0,0,.6);
  transform:translateX(100%); transition:transform .25s ease;
  display:flex; flex-direction:column;
}
#panel.open { transform:translateX(0); }
#ph { padding:16px 18px 12px; border-bottom:1px solid rgba(60,60,160,.2); display:flex; justify-content:space-between; align-items:center; }
#pt { font-size:.85rem; font-weight:700; color:#aac0ff; }
#pc { cursor:pointer; background:none; border:none; color:#556; font-size:1rem; }
#pc:hover { color:#ff6688; }
#pb { padding:16px 18px; overflow-y:auto; flex:1; }
.ir { margin-bottom:12px; }
.il { font-size:.6rem; text-transform:uppercase; letter-spacing:.1em; color:#445; margin-bottom:3px; }
.iv { font-size:.78rem; color:#b0c0ff; }
.badge {
  display:inline-block; padding:2px 10px; border-radius:12px;
  font-size:.68rem; font-weight:700; color:#fff;
}
.cap { font-size:.72rem; color:#7788aa; border-left:2px solid #334; padding-left:8px; margin:3px 0; }
.conn-list { list-style:none; }
.conn-list li { font-size:.7rem; color:#5566aa; padding:4px 0; border-bottom:1px solid rgba(40,40,80,.4); display:flex; gap:6px; align-items:center; }
.ct { font-size:.6rem; color:#334; }

/* legend */
#leg {
  position:fixed; left:12px; bottom:12px; z-index:25;
  background:rgba(8,8,20,.88); border:1px solid rgba(60,60,160,.25);
  border-radius:10px; padding:12px 14px; max-height:50vh; overflow-y:auto;
  backdrop-filter:blur(8px);
}
#leg h3 { font-size:.58rem; letter-spacing:.12em; text-transform:uppercase; color:#334; margin-bottom:8px; }
.li { display:flex; align-items:center; gap:7px; margin-bottom:5px; cursor:pointer; }
.li.dim { opacity:.25; }
.ld { width:9px; height:9px; border-radius:2px; flex-shrink:0; }
.ll { font-size:.67rem; color:#6677aa; }
.lc { font-size:.6rem; color:#334; margin-left:auto; }

/* hint */
#hint { position:fixed; left:12px; top:60px; font-size:.63rem; color:#2a2a55; line-height:2; z-index:25; }

/* tooltip */
#tip {
  position:fixed; pointer-events:none; z-index:40;
  background:rgba(8,8,30,.95); border:1px solid rgba(80,80,200,.4);
  border-radius:8px; padding:8px 14px; font-size:.74rem; display:none;
  box-shadow:0 4px 20px rgba(0,0,60,.6); max-width:220px;
}
</style>
</head>
<body>

<canvas id="c"></canvas>
<div id="labels"></div>

<div id="hdr">
  <span class="logo">ZEA</span>
  <span class="desc">__SYS_DESC__</span>
  <div class="pill">Nodes <b>__NODE_COUNT__</b></div>
  <div class="pill">Edges <b>__EDGE_COUNT__</b></div>
  <div class="pill">__SYS_TYPE__</div>
</div>

<div id="panel">
  <div id="ph"><span id="pt">Component</span><button id="pc">✕</button></div>
  <div id="pb"></div>
</div>

<div id="leg"><h3>Components</h3><div id="li"></div></div>

<div id="hint">Drag · Rotate<br>Scroll · Zoom<br>Right-drag · Pan<br>Click · Inspect</div>

<div id="tip"></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
// ════════════════════════════════════════════════════════════
//  DATA  (injected by Python)
// ════════════════════════════════════════════════════════════
const ANALYSIS   = __ANALYSIS_JSON__;
const COMP_DEFS  = __COMP_DEFS_JSON__;
const EDGE_COLS  = __EDGE_COLS_JSON__;
const POSITIONS  = __POSITIONS_JSON__;   // {node_id: [x, z]}

// ════════════════════════════════════════════════════════════
//  HELPERS
// ════════════════════════════════════════════════════════════
function hexInt(s){ return parseInt(s.replace('#',''), 16); }
function def(type){ return COMP_DEFS[type] || COMP_DEFS['_default']; }
function ecol(type){ return EDGE_COLS[type] || '#78909c'; }
function isWireless(type){ return ['PUBLISHES','CONSUMES','INVOKES','CONNECTS_TO'].includes(type); }

// ════════════════════════════════════════════════════════════
//  SCENE
// ════════════════════════════════════════════════════════════
const canvas   = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type    = THREE.PCFSoftShadowMap;
renderer.setClearColor(0x090912, 1);

const scene  = new THREE.Scene();
scene.fog    = new THREE.FogExp2(0x090912, 0.00055);

const camera = new THREE.PerspectiveCamera(50, 1, 1, 6000);
camera.position.set(0, 500, 900);
camera.lookAt(0, 0, 0);

function resize(){
  const W=canvas.clientWidth, H=canvas.clientHeight;
  renderer.setSize(W,H,false);
  camera.aspect=W/H;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);
resize();

// ── Ground surface ──────────────────────────────────────────
const groundGeo = new THREE.PlaneGeometry(4000, 4000);
const groundMat = new THREE.MeshStandardMaterial({
  color:0x0c0c1e, roughness:0.95, metalness:0.1
});
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI/2;
ground.receiveShadow = true;
scene.add(ground);

// Grid on top of ground
const grid = new THREE.GridHelper(4000, 80, 0x1a2060, 0x111840);
grid.position.y = 0.5;
scene.add(grid);

// ── Lighting ────────────────────────────────────────────────
scene.add(new THREE.AmbientLight(0x111133, 1.0));
scene.add(new THREE.HemisphereLight(0x223366, 0x050510, 0.5));

const sunLight = new THREE.DirectionalLight(0x8899cc, 0.7);
sunLight.position.set(300, 600, 400);
sunLight.castShadow = true;
sunLight.shadow.mapSize.set(2048, 2048);
sunLight.shadow.camera.near = 10;
sunLight.shadow.camera.far  = 3000;
sunLight.shadow.camera.left = sunLight.shadow.camera.bottom = -1200;
sunLight.shadow.camera.right= sunLight.shadow.camera.top   = 1200;
scene.add(sunLight);

// Accent point lights
const aLight1 = new THREE.PointLight(0x2244ff, 1.2, 1200);
aLight1.position.set(-400, 200, -200);
scene.add(aLight1);
const aLight2 = new THREE.PointLight(0xff6622, 0.8, 1000);
aLight2.position.set(400, 150, 300);
scene.add(aLight2);

// ════════════════════════════════════════════════════════════
//  BUILD GEOMETRY FACTORY
// ════════════════════════════════════════════════════════════
function makeGeometry(d){
  const s = d.shape || 'box';
  if(s==='box')       return new THREE.BoxGeometry(d.w||50, d.h||50, d.d||50);
  if(s==='cylinder')  return new THREE.CylinderGeometry(d.rt||20, d.rb||20, d.h||40, d.segs||16);
  if(s==='sphere')    return new THREE.SphereGeometry(d.r||22, d.wsegs||12, d.hsegs||10);
  if(s==='torus')     return new THREE.TorusGeometry(d.r||20, d.tube||6, d.segs||8, d.tsegs||16);
  if(s==='octahedron')return new THREE.OctahedronGeometry(d.r||20);
  if(s==='cone')      return new THREE.ConeGeometry(d.rb||20, d.h||40, d.segs||8);
  if(s==='tetrahedron')return new THREE.TetrahedronGeometry(d.r||22);
  return new THREE.BoxGeometry(45,45,45);
}

// Half-height for sitting on ground
function halfH(d){
  const s=d.shape||'box';
  if(s==='box'||s==='cylinder')return (d.h||45)/2;
  if(s==='sphere')return d.r||22;
  if(s==='torus') return (d.tube||6);
  if(s==='octahedron')return (d.r||20)*0.85;
  if(s==='cone') return (d.h||40)/2;
  return 25;
}

// ════════════════════════════════════════════════════════════
//  PLACE COMPONENTS
// ════════════════════════════════════════════════════════════
const components = ANALYSIS.components || [];
const meshByID   = {};
const compByID   = {};
const allMeshes  = [];

components.forEach(comp => {
  const d  = def(comp.layer && comp.shape ? comp.shape : (comp.node_id.split('_')[0]||'service'));
  // Prefer shape field from analysis, else derive from node_id prefix
  const nodeType = (ANALYSIS.components || []).find ? '' : '';
  const shapeKey = comp._shape_key || comp.node_id.split('_')[0];
  const cd = def(shapeKey);

  const geo = makeGeometry(cd);
  const mat = new THREE.MeshStandardMaterial({
    color:    hexInt(cd.color),
    emissive: hexInt(cd.emissive || cd.color),
    emissiveIntensity: 0.35,
    roughness: 0.55,
    metalness: 0.3,
  });
  const mesh = new THREE.Mesh(geo, mat);

  const xz = POSITIONS[comp.node_id] || [0, 0];
  const yy  = halfH(cd);
  mesh.position.set(xz[0], yy, xz[1]);
  mesh.castShadow    = true;
  mesh.receiveShadow = true;
  mesh.userData = { comp, cd };

  scene.add(mesh);
  meshByID[comp.node_id] = mesh;
  compByID[comp.node_id] = comp;
  allMeshes.push(mesh);
});

// ════════════════════════════════════════════════════════════
//  CONNECTIONS
// ════════════════════════════════════════════════════════════
const connections = ANALYSIS.connections || [];

connections.forEach(conn => {
  const sm = meshByID[conn.source_id];
  const tm = meshByID[conn.target_id];
  if(!sm || !tm) return;

  const sp = sm.position.clone();
  const tp = tm.position.clone();
  const col= hexInt(ecol(conn.edge_type));

  if(isWireless(conn.edge_type)){
    // ── Wireless: dashed arc ──────────────────────────────
    const mid = sp.clone().lerp(tp, 0.5);
    mid.y += 120;
    const curve = new THREE.QuadraticBezierCurve3(sp, mid, tp);
    const pts   = curve.getPoints(40);
    const geo   = new THREE.BufferGeometry().setFromPoints(pts);
    const mat   = new THREE.LineDashedMaterial({
      color:col, dashSize:18, gapSize:10, opacity:0.7, transparent:true
    });
    const line  = new THREE.Line(geo, mat);
    line.computeLineDistances();
    scene.add(line);

    // small floating rings along arc to suggest wireless signal
    [0.25, 0.5, 0.75].forEach(t => {
      const rp = curve.getPoint(t);
      const rg  = new THREE.TorusGeometry(7, 1.2, 6, 14);
      const rm  = new THREE.MeshStandardMaterial({ color:col, emissive:col, emissiveIntensity:0.8, transparent:true, opacity:0.5 });
      const ring= new THREE.Mesh(rg, rm);
      ring.position.copy(rp);
      ring.rotation.x = Math.PI/2;
      scene.add(ring);
    });

  } else {
    // ── Wired: tube along bezier ──────────────────────────
    const arcH = Math.min(160, sp.distanceTo(tp) * 0.35 + 40);
    const mid  = sp.clone().lerp(tp, 0.5);
    mid.y += arcH;
    const curve = new THREE.QuadraticBezierCurve3(sp, mid, tp);
    const geo   = new THREE.TubeGeometry(curve, 24, 1.8, 7, false);
    const mat   = new THREE.MeshStandardMaterial({
      color:col, emissive:col, emissiveIntensity:0.5, roughness:0.4
    });
    const tube  = new THREE.Mesh(geo, mat);
    tube.castShadow = false;
    scene.add(tube);
  }
});

// ════════════════════════════════════════════════════════════
//  HTML LABELS
// ════════════════════════════════════════════════════════════
const labelsDiv = document.getElementById('labels');
const labelMap  = {};
const _v3 = new THREE.Vector3();

components.forEach(comp => {
  const el = document.createElement('div');
  el.className = 'lbl';
  el.textContent = (comp.display_name||comp.node_id).slice(0,24);
  labelsDiv.appendChild(el);
  labelMap[comp.node_id] = el;
});

function project3D(pos){
  _v3.copy(pos).project(camera);
  return {
    x:  (_v3.x*0.5+0.5)*canvas.clientWidth,
    y: (-_v3.y*0.5+0.5)*canvas.clientHeight,
    behind: _v3.z>1
  };
}

// ════════════════════════════════════════════════════════════
//  ORBIT CONTROLS
// ════════════════════════════════════════════════════════════
const orb = {
  theta:-0.3, phi:0.85, radius:900,
  panX:0, panY:0,
  dragMode:null, lx:0, ly:0
};
const _target = new THREE.Vector3(0,30,0);

function applyOrbit(){
  orb.phi = Math.max(0.1, Math.min(1.48, orb.phi));
  camera.position.set(
    _target.x + orb.radius*Math.sin(orb.phi)*Math.sin(orb.theta),
    _target.y + orb.radius*Math.cos(orb.phi),
    _target.z + orb.radius*Math.sin(orb.phi)*Math.cos(orb.theta)
  );
  camera.lookAt(_target);
}
applyOrbit();

canvas.addEventListener('mousedown', e=>{
  orb.dragMode = e.button===2 ? 'pan' : 'orbit';
  orb.lx=e.clientX; orb.ly=e.clientY;
  canvas.style.cursor='grabbing';
});
window.addEventListener('mouseup', ()=>{ orb.dragMode=null; canvas.style.cursor=''; });
window.addEventListener('mousemove', e=>{
  if(!orb.dragMode) return;
  const dx=e.clientX-orb.lx, dy=e.clientY-orb.ly;
  orb.lx=e.clientX; orb.ly=e.clientY;
  if(orb.dragMode==='orbit'){
    orb.theta -= dx*0.006;
    orb.phi   -= dy*0.006;
  } else {
    // pan: move target in the camera's XZ plane
    const pan = 0.7;
    _target.x -= dx*pan;
    _target.z += dy*pan;
  }
  applyOrbit();
});
canvas.addEventListener('wheel', e=>{
  orb.radius = Math.max(60, Math.min(3500, orb.radius+e.deltaY*0.6));
  applyOrbit();
}, {passive:true});
canvas.addEventListener('contextmenu', e=>e.preventDefault());

// ════════════════════════════════════════════════════════════
//  RAYCASTING / HOVER / CLICK
// ════════════════════════════════════════════════════════════
const ray  = new THREE.Raycaster();
const mpos = new THREE.Vector2(-9999,-9999);
const tip  = document.getElementById('tip');

window.addEventListener('mousemove', e=>{
  mpos.x =  (e.clientX/canvas.clientWidth)*2-1;
  mpos.y = -(e.clientY/canvas.clientHeight)*2+1;
  tip.style.left=(e.clientX+14)+'px';
  tip.style.top =(e.clientY- 8)+'px';
});

canvas.addEventListener('click', e=>{
  ray.setFromCamera(mpos, camera);
  const hits = ray.intersectObjects(allMeshes);
  if(hits.length) openPanel(hits[0].object.userData.comp, hits[0].object.userData.cd);
  else closePanel();
});

function openPanel(comp, cd){
  document.getElementById('pt').textContent = comp.display_name||comp.node_id;
  const caps = (comp.capabilities||[]).map(c=>`<div class="cap">${c}</div>`).join('');
  const conns = connections
    .filter(c=>c.source_id===comp.node_id||c.target_id===comp.node_id)
    .map(c=>{
      const other = c.source_id===comp.node_id ? c.target_id : c.source_id;
      const dir   = c.source_id===comp.node_id ? '→' : '←';
      const oc    = compByID[other];
      return `<li>${dir} ${oc?oc.display_name:other} <span class="ct">${c.edge_type} · ${c.wire_type}</span></li>`;
    }).join('');
  document.getElementById('pb').innerHTML = `
    <div class="ir">
      <div class="il">Layer</div>
      <span class="badge" style="background:${cd.color}">${comp.layer||'?'}</span>
    </div>
    <div class="ir">
      <div class="il">Description</div>
      <div class="iv">${comp.description||'—'}</div>
    </div>
    ${caps?`<div class="ir"><div class="il">Capabilities</div>${caps}</div>`:''}
    <div class="ir">
      <div class="il">Connections (${connections.filter(c=>c.source_id===comp.node_id||c.target_id===comp.node_id).length})</div>
      <ul class="conn-list">${conns||'<li style="color:#334">None</li>'}</ul>
    </div>
  `;
  document.getElementById('panel').classList.add('open');
}
function closePanel(){
  document.getElementById('panel').classList.remove('open');
}
document.getElementById('pc').addEventListener('click', closePanel);

// ════════════════════════════════════════════════════════════
//  LEGEND
// ════════════════════════════════════════════════════════════
const hiddenTypes = new Set();
const typeComps   = {};
components.forEach(c=>{ (typeComps[c.layer]||(typeComps[c.layer]=[])).push(c.node_id); });

Object.entries(typeComps).forEach(([layer, ids])=>{
  const cd  = def(layer);
  const row = document.createElement('div');
  row.className='li';
  row.innerHTML=`<div class="ld" style="background:${cd.color};border-radius:${['cylinder','sphere'].includes(cd.shape)?'50%':'2px'}"></div><span class="ll">${layer}</span><span class="lc">${ids.length}</span>`;
  row.addEventListener('click',()=>{
    if(hiddenTypes.has(layer)){ hiddenTypes.delete(layer); row.classList.remove('dim'); }
    else { hiddenTypes.add(layer); row.classList.add('dim'); }
    components.forEach(c=>{
      if(meshByID[c.node_id]){ meshByID[c.node_id].visible = !hiddenTypes.has(c.layer); }
      if(labelMap[c.node_id])  labelMap[c.node_id].style.display = hiddenTypes.has(c.layer)?'none':'';
    });
  });
  document.getElementById('li').appendChild(row);
});

// ════════════════════════════════════════════════════════════
//  ANIMATION
// ════════════════════════════════════════════════════════════
let t=0;
function animate(){
  requestAnimationFrame(animate);
  t+=0.012;

  // Gentle float on torus/event nodes
  components.forEach((comp,i)=>{
    const m=meshByID[comp.node_id];
    if(!m) return;
    const cd=m.userData.cd;
    if(['torus','octahedron','sphere'].includes(cd.shape||'box')){
      const base = halfH(cd);
      m.position.y = base + Math.sin(t+i*0.8)*4;
      m.rotation.y = t*0.4;
    }
  });

  // Update labels
  const W=canvas.clientWidth, H=canvas.clientHeight;
  components.forEach(comp=>{
    const m=meshByID[comp.node_id];
    const el=labelMap[comp.node_id];
    if(!m||!el) return;
    const cd=m.userData.cd;
    const lp=m.position.clone();
    lp.y+=halfH(cd)+14;
    const p=project3D(lp);
    if(p.behind||!m.visible){ el.style.display='none'; return; }
    el.style.display='';
    el.style.left=p.x+'px';
    el.style.top=p.y+'px';
  });

  // Hover tooltip
  ray.setFromCamera(mpos, camera);
  const hits=ray.intersectObjects(allMeshes.filter(m=>m.visible));
  if(hits.length){
    const {comp}=hits[0].object.userData;
    tip.innerHTML=`<b style="color:#aac0ff">${comp.display_name||comp.node_id}</b><br><span style="color:#446;font-size:.68rem">${comp.layer||''}</span>`;
    tip.style.display='block';
    canvas.style.cursor='pointer';
  } else {
    tip.style.display='none';
    if(!orb.dragMode) canvas.style.cursor='grab';
  }

  renderer.render(scene, camera);
}
animate();
</script>
</body>
</html>
"""


def generate_html(analysis: dict, output_path: Union[str, Path]) -> Path:
    """
    Generate a 3D system design HTML from an AI analysis dict.

    Parameters
    ----------
    analysis : dict
        Output of ai/analyzer.py — has keys: system_description,
        system_type, components, connections, domains.
    output_path : Path
        Destination .html file.
    """
    output_path = Path(output_path).resolve()

    components  = analysis.get("components", [])
    connections = analysis.get("connections", [])
    repo_name   = analysis.get("_repo_name", "System")
    sys_desc    = analysis.get("system_description", "Architecture visualization")
    sys_type    = analysis.get("system_type", "unknown")

    # Enrich each component with the right shape key
    for comp in components:
        nid = comp.get("node_id", "")
        # Try to match node_id prefix to COMPONENT_DEFS
        for key in COMPONENT_DEFS:
            if nid.startswith(key) or key in nid:
                comp["_shape_key"] = key
                break
        else:
            comp["_shape_key"] = comp.get("layer", "service")

    # Compute 2D layout positions
    positions = _compute_layout(components)

    # Build JS-ready defs (include default)
    comp_defs_js = dict(COMPONENT_DEFS)
    comp_defs_js["_default"] = DEFAULT_DEF
    # Add layer-based entries so JS def() can also look up by layer name
    LAYER_TO_TYPE = {
        "frontend": "frontend", "gateway": "gateway", "service": "service",
        "data": "database", "messaging": "queue", "infrastructure": "cluster",
        "external": "external_system",
    }
    for layer, base_type in LAYER_TO_TYPE.items():
        if layer not in comp_defs_js and base_type in comp_defs_js:
            comp_defs_js[layer] = comp_defs_js[base_type]

    html = _HTML
    html = html.replace("__REPO_NAME__",    repo_name)
    html = html.replace("__SYS_DESC__",     sys_desc[:120])
    html = html.replace("__SYS_TYPE__",     sys_type)
    html = html.replace("__NODE_COUNT__",   str(len(components)))
    html = html.replace("__EDGE_COUNT__",   str(len(connections)))
    html = html.replace("__ANALYSIS_JSON__",json.dumps(analysis, ensure_ascii=False))
    html = html.replace("__COMP_DEFS_JSON__",json.dumps(comp_defs_js, ensure_ascii=False))
    html = html.replace("__EDGE_COLS_JSON__", json.dumps(EDGE_COLORS, ensure_ascii=False))
    html = html.replace("__POSITIONS_JSON__", json.dumps(
        {nid: list(xy) for nid, xy in positions.items()},
        ensure_ascii=False,
    ))

    output_path.write_text(html, encoding="utf-8")
    return output_path


def generate_html_from_file(
    graph_path: Union[str, Path],
    output_path: Union[str, Path],
) -> Path:
    """
    Convenience wrapper: reads architecture_graph.json (static analysis output)
    and generates the 3D view using the static fallback analysis.
    For AI-enriched output, call generate_html(analysis, output_path) directly.
    """
    import json
    from system_design.ai.analyzer import _static_fallback

    graph_path = Path(graph_path).resolve()
    with graph_path.open(encoding="utf-8") as f:
        graph = json.load(f)

    analysis = _static_fallback({
        "repository_name": graph.get("repository_name", "system"),
        "languages": [],
        "frameworks": [],
        "package_managers": [],
        "infrastructure": [],
        "has_tests": False,
        "has_ci":   False,
        "total_files": 0,
    }, graph)
    analysis["_repo_name"]  = graph.get("repository_name", "system")

    return generate_html(analysis, output_path)
