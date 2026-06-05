🚢 Smart Ship Route Optimizer

Final Year Project | Python · FastAPI · MongoDB · React

An intelligent maritime navigation system that calculates the safest, shortest, and most fuel-efficient routes for cargo ships and boats — avoiding danger zones, optimizing fuel costs, and reducing travel time.

🎯 What Problem Does It Solve?
Cargo ships and boats often take routes that are:

❌ Longer than necessary → wastes fuel & time
❌ Passing through danger zones → risk of accidents
❌ Not cost-optimized → higher operational costs

Our system solves this by computing the best possible maritime route based on distance, fuel cost, and real-time hazard data.

✨ Key Features
FeatureDescription🗺️ Optimized RoutingCalculates shortest & most efficient path between two ports⚠️ Danger Zone AvoidanceAutomatically avoids piracy zones, storms, and restricted areas⛽ Fuel Cost EstimationEstimates fuel consumption and cost for each route🔄 Multiple Route OptionsShows alternate routes ranked by cost, distance & safety📦 Cargo Ship & Boat SupportWorks for all vessel types with different fuel profiles

🛠️ Tech Stack
Backend

🐍 Python + FastAPI — REST API & routing logic
🍃 MongoDB — storing routes, ports, and hazard zone data

Frontend

⚛️ React.js — interactive UI & map visualization

Algorithms

Dijkstra's / A* Algorithm for optimal pathfinding
Weighted graph with cost, distance & danger as parameters


👥 Team & My Contributions
Built by a team of 4 developers for our Final Year Project.
My role covered:

🍃 MongoDB — database design, schema, storing port & route data
🎨 Frontend — UI screens, map display, route result pages
🐍 Python — assisted in backend logic and API integration


🏗️ System Architecture
User Input (Source & Destination Port)
            ↓
     FastAPI Backend
            ↓
  Route Optimization Engine
  (Shortest + Safest + Cheapest)
            ↓
     MongoDB (Ports, Hazards, Routes)
            ↓
  React Frontend → Map Visualization

📸
<img width="389" height="759" alt="Screenshot 2026-03-24 153830" src="https://github.com/user-attachments/assets/d03b7cb7-12bb-4d68-9e97-48bc47629c72" />

<img width="1492" height="869" alt="Screenshot 2026-03-24 135505" src="https://github.com/user-attachments/assets/ae37e503-1093-4174-9a29-67e7ab802394" />




🚀 How to Run Locally
bash# Clone the repo
git clone https://github.com/Govil-Tyagi/ship-route-optimizer.git

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start

📌 Note
This was our Final Year B.Tech Project. Built with real-world maritime routing challenges in mind.

Made with ❤️ by Team of 4 | B.Tech Final Year
