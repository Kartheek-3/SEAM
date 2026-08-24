# SEAM OS - Autonomous Software Engineering IDE

SEAM OS is the frontend visualization layer for the SEAM Framework, an autonomous software engineering operating system.

This React application transforms the multi-agent orchestration telemetry (Analysis, Planning, Coding, QA, Delivery) into a sophisticated, IDE-like workspace. It features a custom command palette, project explorer, tabbed code viewer, AI task drawer, interactive agent panels, and observability dashboards.

## Architecture & Stack

- **Framework**: React 19 + Vite
- **Styling**: Tailwind CSS v4 (Custom Dark Theme)
- **Icons**: Lucide React
- **Routing**: React Router v6
- **State Management**: React Context (`IDEContext.jsx`)
- **API Client**: Axios

## Frontend/Backend Separation

Currently, the frontend runs in **Demo Mode**. All data is driven by the internal mock data architecture (`src/data/`) via custom React hooks (`src/hooks/useData.js`). The API stub layer (`src/services/api.js`) is prepared but inactive.

This strict separation ensures that frontend development and CI/CD visualization testing does not interfere with or mock the actual production backend agents or experiment telemetry files.

## Setup & Development

### Installation

```bash
cd frontend
npm install
```

### Environment Configuration

Copy the example environment variables:

```bash
cp .env.example .env.local
```

### Start Development Server

```bash
npm run dev
```

### Build for Production

```bash
npm run build
```

## Folder Structure

\`\`\`
frontend/
├── src/
│   ├── components/       # Core UI components
│   │   └── ide/          # Advanced workspace components (CommandPalette, Explorer, etc.)
│   ├── context/          # React Context (IDEContext)
│   ├── data/             # Mock data sources for Demo Mode
│   ├── hooks/            # Data access hooks
│   ├── layouts/          # Persistent shell (IDELayout)
│   ├── pages/            # Routable pages (Workspace, Experiments, QA, etc.)
│   ├── services/         # API clients
│   ├── App.jsx           # Main routing assembly
│   └── index.css         # Tailwind directives and theme tokens
├── .env.example          # Example environment variables
├── package.json          # Dependencies and scripts
└── vite.config.js        # Vite build configuration
\`\`\`
