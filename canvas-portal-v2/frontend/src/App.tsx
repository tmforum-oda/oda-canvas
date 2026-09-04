import React from 'react'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import AppLayout from '@/layout/AppLayout'
import CanvasCluster from '@/pages/CanvasCluster'
import ComponentsPage from '@/pages/Components'
import ComponentsDeployPage from '@/pages/Components/Deploy'
import ComponentsLifecyclePage from '@/pages/Components/Lifecycle'
import ExposedAPIsPage from '@/pages/ExposedAPIs'
import OperatorsPage from '@/pages/Operators'
import OperatorDetail from '@/pages/Operators/OperatorDetail'
import ObservabilityPage from '@/pages/Observability'
import BDDPage from '@/pages/BDD'
import ModelGatewayPage from '@/pages/ModelGateway'
import TMFAIAgentsPage from '@/pages/TMFAIAgents'

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <CanvasCluster /> },

      // Components section
      { path: 'components', element: <ComponentsPage /> },
      { path: 'components/deploy', element: <ComponentsDeployPage /> },
      { path: 'components/lifecycle', element: <ComponentsLifecyclePage /> },
      { path: 'components/:namespace/:name', element: <ComponentsPage /> },

      // API Exposure section
      { path: 'exposedapis', element: <ExposedAPIsPage /> },
      { path: 'dependentapis', element: <ExposedAPIsPage /> },
      { path: 'gateway', element: <ExposedAPIsPage /> },
      { path: 'ratelimiting', element: <ExposedAPIsPage /> },
      { path: 'servicemesh', element: <ExposedAPIsPage /> },
      { path: 'policies', element: <ExposedAPIsPage /> },

      // Monitor section
      { path: 'observability', element: <ObservabilityPage /> },
      { path: 'operators', element: <OperatorsPage /> },
      { path: 'operators/:namespace/:name', element: <OperatorDetail /> },
      { path: 'bdd', element: <BDDPage /> },
      { path: 'model-gateway-services', element: <ModelGatewayPage /> },
      { path: 'tmf-ai-agents', element: <TMFAIAgentsPage /> },

      // Catch-all
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
