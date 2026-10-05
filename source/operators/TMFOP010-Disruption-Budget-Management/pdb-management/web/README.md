# ODA Canvas - PDB Management MCP Web Interface

A modern TypeScript/React web application for managing Kubernetes Pod Disruption Budgets (PDBs) through the MCP (Model Context Protocol) interface.

## Features

- **AI Chat Interface**: Interact with AI assistants using natural language to manage PDBs
- **Tool Explorer**: Discover and execute MCP tools for PDB management
- **Policy Manager**: Create and manage availability policies with intelligent recommendations
- **Cluster Analysis**: Analyze cluster PDB coverage with interactive dashboards
- **Multi-AI Provider Support**: Works with Claude, OpenAI, Azure OpenAI, and Gemini
- **Real-time Updates**: WebSocket support for live data updates
- **Responsive Design**: Mobile-friendly Material-UI interface
- **Dark/Light Theme**: Toggle between themes with ODA Canvas branding

## Tech Stack

- **Frontend**: React 18, TypeScript, Material-UI
- **State Management**: Zustand
- **Data Fetching**: React Query (TanStack Query)
- **Charts**: Recharts, MUI X Charts
- **Build Tool**: Vite
- **Styling**: Material-UI with custom ODA Canvas theme

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Access to MCP server (running on port 8090 by default)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to `http://localhost:3000`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Configuration

### AI Provider Setup

The application supports multiple AI providers. Configure them in the AI settings:

1. **Claude (Anthropic)**
   - Model: claude-3-sonnet-20240229 (recommended)
   - API Key: Optional (can use server-side configuration)

2. **OpenAI**
   - Model: gpt-4-turbo-preview
   - API Key: Required

3. **Azure OpenAI**
   - Model: gpt-4
   - Endpoint: Your Azure OpenAI endpoint
   - API Key: Required

4. **Google Gemini**
   - Model: gemini-pro
   - API Key: Required

### MCP Server Connection

The web application connects to the MCP server at `/api/mcp` (proxied to `http://localhost:8090` by default).

Update the Vite configuration in `vite.config.ts` if your MCP server runs on a different port:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:YOUR_PORT',
      changeOrigin: true,
    },
  },
},
```

## Project Structure

```
src/
├── api/                 # API clients (MCP, AI)
├── components/         # React components
│   ├── ChatInterface.tsx
│   ├── ToolExplorer.tsx
│   ├── PolicyManager.tsx
│   └── ClusterAnalysis.tsx
├── store/              # Zustand state management
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
├── theme.ts            # Material-UI theme configuration
├── App.tsx             # Main application component
└── main.tsx           # Application entry point
```

## Features in Detail

### AI Chat Interface

- Natural language interaction with AI assistants
- Tool execution through MCP protocol
- Support for multiple AI providers
- Real-time streaming responses
- Tool call visualization with parameters and results

### Tool Explorer

- Discover available MCP tools
- Interactive parameter forms with validation
- Execution history with detailed results
- Export execution data for analysis

### Policy Manager

- Step-by-step policy creation wizard
- Intelligent recommendations based on cluster analysis
- Policy validation and conflict detection
- Support for different enforcement modes (strict, advisory, flexible)

### Cluster Analysis

- Real-time cluster metrics dashboard
- Namespace-level PDB coverage analysis
- Risk assessment with visual indicators
- Interactive charts and data tables
- Export functionality for reports

## API Integration

The application integrates with:

- **MCP Server**: For tool execution and cluster management
- **AI Providers**: For natural language processing and assistance
- **WebSocket**: For real-time updates (when available)

## Development

### Code Style

The project uses ESLint and TypeScript for code quality:

```bash
npm run lint          # Check for linting issues
npm run type-check    # Verify TypeScript types
```

### Adding New Components

1. Create component in `src/components/`
2. Add necessary types in `src/types/`
3. Update routing in `App.tsx` if needed
4. Add to navigation menu if applicable

### State Management

The application uses Zustand for state management:

- `useAppStore`: Global app state (theme, navigation, etc.)
- `useChatStore`: Chat messages and AI interaction state
- `useToolStore`: MCP tool state and execution history
- `usePolicyFormStore`: Policy form state
- `useNotificationStore`: Toast notifications

## Contributing

1. Follow the existing code style and conventions
2. Add TypeScript types for all new interfaces
3. Use Material-UI components consistently
4. Test with multiple AI providers
5. Ensure responsive design works on mobile devices

## License

This project is part of the ODA Canvas ecosystem and follows the same licensing terms.

## Support

For issues and questions related to the PDB Management MCP Web Interface, please refer to the main project documentation or create an issue in the repository.