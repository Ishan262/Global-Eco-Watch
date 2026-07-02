# 🌍 Global Eco-Watch (OmniCarbon)

A production-ready Full-Stack Civic Tech platform engineered to bridge the gap between crowd-sourced environmental datasets and localized municipal accountability.

🚀 **Live Deployment Link**: https://global-eco-watchin.onrender.com/
🎯 **Project Walkthrough Video**: [Insert your Loom/YouTube Link Here]

---

## 📌 Project Overview
Urban air pollution often suffers from a lack of localized, street-level accountability. Global Eco-Watch empowers citizens by leveraging automated browser telemetry to capture immediate geographic environmental data, providing a frictionless framework for documenting emissions hotspots (e.g., open waste burning, heavy industrial exhaust) and routing them directly to municipal governance bodies.

### Key Features
* **Automated Telemetry Sync**: Integrates the native HTML5 Geolocation API to lock user coordinates instantly upon launch without requiring manual input.
* **Geospatial Translation**: Implements the open-source OpenStreetMap Nominatim Engine to dynamically reverse-geocode raw GPS coordinates into human-readable street addresses.
* **Dynamic Threshold Alerts**: Monitors real-time atmospheric data streams. If the Air Quality Index (AQI) crosses critical safety thresholds (Level 4/5), the platform triggers high-visibility emergency modal overlays and auto-focuses user input workflows.
* **Civic Audit Engine**: A dedicated backend compilation system that queries active database ledgers to dynamically format, structure, and export clean PDF diagnostic reports for city planning inspections.

---

## 🛠️ System Architecture & Tech Stack

### Frontend Architecture
* **Interface Layout**: Styled completely using an adaptive dark-mode system engineered via **Tailwind CSS**.
* **Mapping Engine**: Interactive global map components deployed using **Leaflet.js**.

### Backend Core
* **Server Framework**: **Python (Flask Engine)** managing asynchronous data routing.
* **Database Ledger**: **SQLite** processing internal transactional complaint histories securely.
* **Production Gateway**: Hosted permanently using **Gunicorn** on isolated Linux cloud containers (**Render Networks**).

---

## 📂 Repository File Structure
```text
artifacts/eco-sentinel/
├── app.py                # Main backend Python Flask routing and API control engine
├── requirements.txt      # Production system packages (Flask, reportlab, gunicorn, etc.)
├── package.json          # Node/Vite dependency tracking systems
├── index.html            # Core frontend application user interface frame
└── templates/            # Core configuration folder mapping out standard UI delivery components
```

---

## 🎯 Future Technical Roadmap
* **Phase 2 (Hardware Mesh Integration)**: Bridging cloud software systems with low-cost microcontrollers (NodeMCU ESP8266) running calibrated MQ-135 physical sensor arrays to cross-verify localized atmospheric readings.
* **Phase 3 (Algorithmic Routing)**: Implementing automated SMTP mailing protocols to instantly forward compiled PDF audit files directly to regional environmental cell addresses based on reverse-geocoded zoning profiles.
* 
