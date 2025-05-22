# LCMR Lighting Control Project

This project is a full-stack web application for controlling and scheduling multi-channel lighting, built with Vue 3 and a Flask backend with WebSocket support.

## Key Files

### [webhandler.py](webhandler.py)
- **Flask backend** serving the API and WebSocket endpoints.
- Handles:
  - Lighting state (GET/POST `/api/state`)
  - Profile CRUD (GET/POST/DELETE `/api/profiles`)
  - Schedule CRUD (GET/POST/PUT/DELETE `/api/schedules`)
  - WebSocket events for real-time slider updates
- Uses file-based storage for profiles and schedules (JSON files on disk).
- Implements a local lockout mechanism to prevent remote changes during local use.

### [src/pages/index.vue](src/pages/index.vue)
- **Main UI page** for controlling lighting channels and managing profiles.
- Features:
  - Vertical sliders for each light channel (IR, Red, Green, Blue, White, UV)
  - Floating action buttons for Save, Load, and Reset
  - Dialogs for saving/loading profiles with previews
  - Animated alerts and modern UI
  - Real-time updates via WebSocket

### [src/pages/timer.vue](src/pages/timer.vue)
- **Timer and schedule management UI**.
- Allows users to view, add, edit, and delete lighting schedules.
- Integrates with the backend's schedule API.

### [src/layouts/default.vue](src/layouts/default.vue)
- **App layout** providing the navigation bar and main content area.
- Wraps all pages with a consistent look and feel.
- Houses the notificiation system.
- Place global navigation or persistent UI elements here.

### [src/plugins/globalState.js](src/plugins/globalState.js)
- **Global state management** for profiles, schedules, and alerts.
- Provides composable functions for CRUD operations and polling.
- Handles API calls to the backend and manages UI alerts.
- All API interactions and state updates are centralized here for reactivity.

---

## Quick Start

1. **Backend:**
   - Run `python webhandler.py` (requires Flask, Flask-CORS, Flask-SocketIO, eventlet)
2. **Frontend:**
   - Install dependencies: `npm install`
   - Start dev server: `npm run dev:build`
   - Copy `.v-slider.v-input--vertical > .v-input__control {min-height: 0 !important; height: 100% !important;}` into the built index.css file.
3. Open the app in your browser (default: `http://localhost:8080`)
