<div align="center">

  # 🚆 GraphPath: Bi-Directional Track Router & Loop Siding Dispatcher

  **An interactive railway routing and dual-track bypass simulation tool featuring real-time Dijkstra pathfinding, block-line management, and interlocking siding logic.**

  [![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
  [![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
  [![Canvas API](https://img.shields.io/badge/Canvas_API-000000?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## 📌 Overview

**GraphPath** is an interactive railway network simulator and routing engine. It models multi-station rail corridors (such as Sealdah, Bandel, Burdwan, and New Cooch Behar) with dual UP and DOWN tracks, gradient limits, and speed constraints. The application calculates optimal transit paths using a modified Dijkstra algorithm that accounts for mid-line blockages, loop-siding crossovers, and oncoming train conflict windows.

---

## ✨ Key Features

* **🧠 Advanced Routing Algorithm:** Custom Dijkstra pathfinder that evaluates segment distance, speed, gradient profiles, and active track blockages.
* **🛤️ Dual-Line & Siding Interlocking:** Simulates crossover logic when a primary track line is blocked, factoring in interlocking delays and oncoming traffic conflict windows.
* **⚠️ Interactive Track Blockage Management:** On-the-fly interactive control grid allowing users to toggle UP or DOWN line blockages between stations to test dynamic rerouting.
* **📊 Live Dispatcher Telemetry:** Real-time logging console providing status updates, crossover notices, siding hold durations, and computed arrival times.
* **🎨 Canvas Network Visualization:** Visual schematic rendering nodes, dual track lines, blocked routes, and active dispatch paths.

---

## 🛠️ Tech Stack

* **Frontend:** Vanilla HTML5, CSS3
* **Rendering Engine:** HTML5 2D Canvas API
* **Algorithm & Logic:** Vanilla JavaScript (ES6+, Modified Dijkstra's Algorithm, Priority Queue routing)

---

## 🏗️ Routing & Siding Logic

The routing engine dynamically evaluates path costs, transit times, and conflict constraints:

```mermaid
graph TD;
    A[Select Start & Target Stations] --> B[Run Modified Dijkstra Pathfinding];
    B --> C{Is Primary Track Blocked?};
    C -- No --> D[Calculate Standard Segment Transit Time];
    C -- Yes --> E{Is Alternate Track Available?};
    E -- Yes --> F[Apply Crossover & Check Oncoming Traffic Slots];
    F --> G[Compute Loop Siding Hold Delay & Total Time];
    E -- No --> H[Mark Route as Blocked / Unavailable];
    D --> I[Render Optimal Dispatch Route & Logs];
    G --> I;
