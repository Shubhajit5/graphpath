import heapq
import numpy as np
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# Double-Track Railway Network with Loop Sidings and Multi-Train Schedule
# Each edge has dual directions ("up" and "down") with capacity and crossover access.
network = {
    "Sealdah": [
        {"node": "Naihati", "dist": 38, "speed": 100, "grad": 0.001, "tracks": ["up", "down"]},
        {"node": "Bandel", "dist": 40, "speed": 80, "grad": 0.002, "tracks": ["up", "down"]},
    ],
    "Naihati": [
        {"node": "Sealdah", "dist": 38, "speed": 100, "grad": -0.001, "tracks": ["up", "down"]},
        {"node": "Ranaghat", "dist": 36, "speed": 110, "grad": 0.000, "tracks": ["up", "down"]},
    ],
    "Bandel": [
        {"node": "Sealdah", "dist": 40, "speed": 80, "grad": -0.002, "tracks": ["up", "down"]},
        {"node": "Burdwan", "dist": 67, "speed": 120, "grad": 0.003, "tracks": ["up", "down"]},
    ],
    "Ranaghat": [
        {"node": "Naihati", "dist": 36, "speed": 110, "grad": 0.000, "tracks": ["up", "down"]},
        {"node": "Burdwan", "dist": 78, "speed": 90, "grad": -0.001, "tracks": ["up", "down"]},
    ],
    "Burdwan": [
        {"node": "Bandel", "dist": 67, "speed": 120, "grad": -0.003, "tracks": ["up", "down"]},
        {"node": "Ranaghat", "dist": 78, "speed": 90, "grad": 0.001, "tracks": ["up", "down"]},
        {"node": "New Cooch Behar", "dist": 620, "speed": 110, "grad": 0.005, "tracks": ["up", "down"]},
    ],
    "New Cooch Behar": [
        {"node": "Burdwan", "dist": 620, "speed": 110, "grad": -0.005, "tracks": ["up", "down"]},
        {"node": "Kamakhya", "dist": 290, "speed": 90, "grad": 0.008, "tracks": ["up", "down"]},
    ],
    "Kamakhya": [
        {"node": "New Cooch Behar", "dist": 290, "speed": 90, "grad": -0.008, "tracks": ["up", "down"]},
        {"node": "New Tinsukia", "dist": 480, "speed": 85, "grad": 0.010, "tracks": ["up", "down"]},
    ],
    "New Tinsukia": [
        {"node": "Kamakhya", "dist": 480, "speed": 85, "grad": -0.010, "tracks": ["up", "down"]},
    ]
}

# Simulated Oncoming Schedule on Down Track [start_time_min, end_time_min]
# Represents existing active traffic on specific sections
oncoming_traffic = {
    ("Burdwan", "New Cooch Behar", "down"): [{"start": 10, "end": 45}],
    ("Naihati", "Ranaghat", "down"): [{"start": 5, "end": 20}]
}

def simulate_segment_time(distance_km, speed_kmh):
    """Calculates baseline travel time in minutes."""
    v = speed_kmh / 60.0
    return round(distance_km / v, 2)

def slw_bypass_dijkstra(start, target, blocked_tracks):
    """
    Bi-Directional Single Line Working Router:
    Handles mid-line blockages on double tracks by using loop sidings,
    calculating crossover delays, and avoiding oncoming traffic on shared tracks.
    """
    if start not in network or target not in network:
        return {"path": [], "total_time": 0, "status_logs": []}

    pq = [(0, start, [start], [])] # (current_time, node, path, logs)
    visited = {}

    while pq:
        curr_time, curr_node, path, logs = heapq.heappop(pq)

        if curr_node == target:
            return {
                "path": path,
                "total_time": round(curr_time, 2),
                "status_logs": logs
            }

        if curr_node in visited and visited[curr_node] <= curr_time:
            continue
        visited[curr_node] = curr_time

        for neighbor in network[curr_node]:
            next_node = neighbor["node"]
            dist = neighbor["dist"]
            speed = neighbor["speed"]
            seg_time = simulate_segment_time(dist, speed)

            edge_key_up = (curr_node, next_node, "up")
            edge_key_down = (curr_node, next_node, "down")

            up_blocked = edge_key_up in blocked_tracks or (next_node, curr_node, "up") in blocked_tracks
            down_blocked = edge_key_down in blocked_tracks or (next_node, curr_node, "down") in blocked_tracks

            edge_delay = 0.0
            chosen_track = None
            log_entry = ""

            if not up_blocked:
                # Normal Up-Line Operation
                chosen_track = "Up Line"
                transit_time = seg_time
            elif up_blocked and not down_blocked:
                # Up Line Blocked -> Loop Siding Bypass to Down Line (Single Line Working)
                chosen_track = "Down Line (Bypass via Loop Siding)"
                crossover_delay = 3.0  # Speed restriction over turnout switch
                entry_time = curr_time + crossover_delay
                exit_time = entry_time + seg_time

                # Check Oncoming Traffic Window
                traffic_conflict = False
                opp_key = (next_node, curr_node, "down")
                if opp_key in oncoming_traffic:
                    for slot in oncoming_traffic[opp_key]:
                        # Conflict check: Overlapping time window
                        if not (exit_time < slot["start"] or entry_time > slot["end"]):
                            traffic_conflict = True
                            # Hold train at Loop Siding until opposing train clears
                            wait_time = slot["end"] - entry_time + 1.0
                            edge_delay = crossover_delay + wait_time
                            log_entry = f"Hold at {curr_node} Siding: {round(wait_time, 1)}m (Waiting for Oncoming Train)"
                            break

                if not traffic_conflict:
                    edge_delay = crossover_delay
                    log_entry = f"Loop Bypass at {curr_node}: Switched to Down Track via Interlocking Turnout"

                transit_time = seg_time + edge_delay
            else:
                # Both Tracks Blocked
                continue

            new_time = curr_time + transit_time
            new_logs = list(logs)
            if log_entry:
                new_logs.append(log_entry)

            heapq.heappush(pq, (new_time, next_node, path + [next_node], new_logs))

    return {"path": [], "total_time": 0, "status_logs": ["Complete Line Blockade: No Route Possible"]}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bi-Directional Track Router & Loop Siding Dispatcher</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #0b0f19; color: #f8fafc; margin: 15px; }
        .container { max-width: 950px; margin: auto; }
        .controls { background: #151e30; padding: 15px; border-radius: 8px; margin-bottom: 15px; display: flex; flex-wrap: wrap; gap: 10px; border: 1px solid #22314e; }
        select, button { padding: 8px 12px; border-radius: 6px; border: 1px solid #334155; background: #0b0f19; color: #fff; font-size: 13px; }
        button { background: #2563eb; font-weight: bold; cursor: pointer; border: none; }
        button:hover { background: #1d4ed8; }
        .block-section { background: #151e30; padding: 12px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #22314e; }
        .block-title { font-size: 12px; font-weight: bold; color: #f43f5e; text-transform: uppercase; margin-bottom: 8px; }
        .block-grid { display: flex; flex-wrap: wrap; gap: 6px; }
        .track-btn { background: #1e293b; color: #cbd5e1; padding: 5px 10px; border-radius: 4px; border: 1px solid #334155; cursor: pointer; font-size: 11px; }
        .track-btn.active { background: #e11d48; color: white; font-weight: bold; }
        #canvas { background: #151e30; border-radius: 8px; display: block; width: 100%; height: auto; border: 1px solid #22314e; }
        .log-box { background: #151e30; padding: 12px; border-radius: 8px; margin-top: 15px; border: 1px solid #22314e; font-family: monospace; font-size: 12px; }
        .log-item { color: #fbbf24; margin-bottom: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h3>Dynamic Loop Siding & Dual-Track Bypass Dispatcher</h3>
        <div class="controls">
            <select id="startSelect"></select>
            <select id="targetSelect"></select>
            <button onclick="calculateRoute()">Compute Dispatch Route</button>
        </div>

        <div class="block-section">
            <div class="block-title">Mid-Line Track Blockages (Select Specific Up / Down Lines):</div>
            <div id="blockGrid" class="block-grid"></div>
        </div>

        <canvas id="canvas" width="900" height="380"></canvas>

        <div class="log-box">
            <div style="color: #38bdf8; font-weight: bold; margin-bottom: 8px;">Dispatch Routing Telemetry & Siding Directives:</div>
            <div id="timeOut" style="color: #4ade80; margin-bottom: 8px; font-weight: bold;"></div>
            <div id="logContent"></div>
        </div>
    </div>

    <script>
        const nodes = {
            "Sealdah": {x: 80, y: 300},
            "Naihati": {x: 200, y: 180},
            "Bandel": {x: 200, y: 340},
            "Ranaghat": {x: 340, y: 140},
            "Burdwan": {x: 420, y: 270},
            "New Cooch Behar": {x: 580, y: 200},
            "Kamakhya": {x: 720, y: 150},
            "New Tinsukia": {x: 840, y: 100}
        };

        const dualEdges = [
            ["Sealdah", "Naihati"], ["Sealdah", "Bandel"],
            ["Naihati", "Ranaghat"], ["Bandel", "Burdwan"],
            ["Ranaghat", "Burdwan"], ["Burdwan", "New Cooch Behar"],
            ["New Cooch Behar", "Kamakhya"], ["Kamakhya", "New Tinsukia"]
        ];

        let blockedTracks = [];
        let currentPath = [];

        function init() {
            const start = document.getElementById('startSelect');
            const target = document.getElementById('targetSelect');
            for (let name in nodes) {
                start.add(new Option(name, name));
                target.add(new Option(name, name));
            }
            start.value = "Burdwan";
            target.value = "New Cooch Behar";

            const container = document.getElementById('blockGrid');
            container.innerHTML = '';
            dualEdges.forEach(([u, v]) => {
                ['up', 'down'].forEach(dir => {
                    const btn = document.createElement('button');
                    btn.className = 'track-btn';
                    btn.innerText = `${u}-${v} (${dir.toUpperCase()})`;
                    btn.onclick = () => toggleBlock(u, v, dir, btn);
                    container.appendChild(btn);
                });
            });
        }

        function toggleBlock(u, v, dir, btn) {
            const index = blockedTracks.findIndex(t => t[0] === u && t[1] === v && t[2] === dir);
            if (index > -1) {
                blockedTracks.splice(index, 1);
                btn.classList.remove('active');
            } else {
                blockedTracks.push([u, v, dir]);
                btn.classList.add('active');
            }
            calculateRoute();
        }

        const ctx = document.getElementById('canvas').getContext('2d');

        function drawGraph() {
            ctx.clearRect(0, 0, 900, 380);

            dualEdges.forEach(([u, v]) => {
                const p1 = nodes[u];
                const p2 = nodes[v];

                // Offset for dual tracks (Up vs Down)
                const dx = p2.x - p1.x;
                const dy = p2.y - p1.y;
                const len = Math.hypot(dx, dy);
                const nx = -dy / len * 4;
                const ny = dx / len * 4;

                // Draw Up Line (Offset +4)
                drawTrackLine(p1.x + nx, p1.y + ny, p2.x + nx, p2.y + ny, u, v, "up");
                // Draw Down Line (Offset -4)
                drawTrackLine(p1.x - nx, p1.y - ny, p2.x - nx, p2.y - ny, u, v, "down");
            });

            // Draw Nodes / Stations
            for (let name in nodes) {
                const {x, y} = nodes[name];
                ctx.beginPath();
                ctx.arc(x, y, 10, 0, Math.PI * 2);
                ctx.fillStyle = currentPath.includes(name) ? '#38bdf8' : '#1e293b';
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.stroke();

                ctx.fillStyle = '#ffffff';
                ctx.font = '11px sans-serif';
                ctx.fillText(name, x - 20, y - 15);
            }
        }

        function drawTrackLine(x1, y1, x2, y2, u, v, dir) {
            const isBlocked = blockedTracks.some(t =>
                (t[0] === u && t[1] === v && t[2] === dir) || (t[0] === v && t[1] === u && t[2] === dir)
            );

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);

            if (isBlocked) {
                ctx.strokeStyle = '#ef4444';
                ctx.lineWidth = 2;
                ctx.setLineDash([4, 4]);
            } else {
                ctx.strokeStyle = '#475569';
                ctx.lineWidth = 2;
                ctx.setLineDash([]);
            }
            ctx.stroke();
            ctx.setLineDash([]);
        }

        async function calculateRoute() {
            const start = document.getElementById('startSelect').value;
            const target = document.getElementById('targetSelect').value;

            const response = await fetch('/api/route', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({start, target, blocked: blockedTracks})
            });

            const data = await response.json();
            currentPath = data.path;

            document.getElementById('timeOut').innerText = data.path.length > 0 ?
                `Optimal Route: ${data.path.join(' → ')} | Total Time: ${data.total_time} mins` :
                'No Available Route';

            const logContainer = document.getElementById('logContent');
            logContainer.innerHTML = '';
            if (data.status_logs.length > 0) {
                data.status_logs.forEach(log => {
                    const div = document.createElement('div');
                    div.className = 'log-item';
                    div.innerText = `> ${log}`;
                    logContainer.appendChild(div);
                });
            } else {
                logContainer.innerHTML = '<div style="color:#94a3b8;">> All tracks operating under normal dual-line conditions.</div>';
            }

            drawGraph();
        }

        init();
        calculateRoute();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/route", methods=["POST"])
def get_route():
    data = request.json or {}
    start = data.get("start")
    target = data.get("target")
    blocked = [tuple(b) for b in data.get("blocked", [])]

    result = slw_bypass_dijkstra(start, target, blocked)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
