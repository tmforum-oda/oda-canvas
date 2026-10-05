import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  Chip,
  LinearProgress,
  Skeleton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  alpha,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
  Shield as ShieldIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';

import mcpClient from '@/api/mcp';
import { ClusterMetrics, NamespaceAnalysis } from '@/types';
import { chartColors } from '@/theme';

// Stat Card
const StatCard: React.FC<{
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color?: string;
  subtitle?: string;
}> = ({ title, value, icon, color, subtitle }) => (
  <Box
    sx={{
      p: 3,
      borderRadius: 3,
      bgcolor: 'background.paper',
      border: 1,
      borderColor: 'divider',
    }}
  >
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
      <Box sx={{ color: color || 'primary.main' }}>{icon}</Box>
      <Typography variant="caption" color="text.secondary">
        {title}
      </Typography>
    </Box>
    <Typography variant="h4">{value}</Typography>
    {subtitle && (
      <Typography variant="caption" color="text.secondary">
        {subtitle}
      </Typography>
    )}
  </Box>
);

// Risk Badge
const RiskBadge: React.FC<{ level: 'low' | 'medium' | 'high' }> = ({ level }) => {
  const config = {
    low: { color: 'success', label: 'Low Risk', icon: <CheckCircleIcon /> },
    medium: { color: 'warning', label: 'Medium Risk', icon: <WarningIcon /> },
    high: { color: 'error', label: 'High Risk', icon: <ErrorIcon /> },
  };
  const { color, label, icon } = config[level];

  return (
    <Chip
      icon={icon}
      label={label}
      color={color as any}
      size="small"
      sx={{ '& .MuiChip-icon': { fontSize: 16 } }}
    />
  );
};

// Namespace Row
const NamespaceRow: React.FC<{ ns: NamespaceAnalysis }> = ({ ns }) => (
  <Box
    sx={{
      p: 2.5,
      borderRadius: 2,
      bgcolor: 'background.paper',
      border: 1,
      borderColor: 'divider',
      display: 'flex',
      alignItems: 'center',
      gap: 3,
      flexWrap: 'wrap',
    }}
  >
    <Box sx={{ flex: 1, minWidth: 120 }}>
      <Typography variant="body1" fontWeight={600}>
        {ns.namespace}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {ns.deploymentsCount} deployments · {ns.podsCount} pods
      </Typography>
    </Box>

    <Box sx={{ minWidth: 100 }}>
      <Typography variant="caption" color="text.secondary">
        PDB Coverage
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <LinearProgress
          variant="determinate"
          value={ns.coveragePercentage}
          sx={{
            width: 60,
            height: 6,
            borderRadius: 3,
            bgcolor: (t) => alpha(t.palette.primary.main, 0.1),
          }}
        />
        <Typography variant="body2" fontWeight={600}>
          {ns.coveragePercentage}%
        </Typography>
      </Box>
    </Box>

    <Box sx={{ minWidth: 80 }}>
      <Typography variant="caption" color="text.secondary">
        PDBs
      </Typography>
      <Typography variant="body2" fontWeight={600}>
        {ns.pdbsCount}
      </Typography>
    </Box>

    <RiskBadge level={ns.riskLevel} />
  </Box>
);

// Helper to parse analysis data
const parseAnalysisData = (data: any) => {
  if (!data) return { metrics: null, namespaces: [] };

  // Try to extract metrics from the analysis data
  let metrics: ClusterMetrics = {
    totalPods: 0,
    totalDeployments: 0,
    totalPDBs: 0,
    totalPolicies: 0,
    healthyPods: 0,
    unhealthyPods: 0,
    nodesCount: 0,
    lastUpdated: new Date(),
  };

  let namespaces: NamespaceAnalysis[] = [];

  // Handle different response formats
  if (typeof data === 'string') {
    // Text response - parse it
    const lines = data.split('\n');
    let currentNs: any = null;

    for (const line of lines) {
      // Parse summary stats
      if (line.includes('Total Deployments:')) {
        metrics.totalDeployments = parseInt(line.split(':')[1]) || 0;
      }
      if (line.includes('Total PDBs:') || line.includes('PDBs:')) {
        metrics.totalPDBs = parseInt(line.match(/\d+/)?.[0] || '0');
      }
      if (line.includes('Policies:')) {
        metrics.totalPolicies = parseInt(line.match(/\d+/)?.[0] || '0');
      }

      // Parse namespace data
      if (line.includes('Namespace:')) {
        if (currentNs) namespaces.push(currentNs);
        currentNs = {
          namespace: line.split(':')[1]?.trim() || 'unknown',
          podsCount: 0,
          deploymentsCount: 0,
          pdbsCount: 0,
          policiesCount: 0,
          coveragePercentage: 0,
          riskLevel: 'medium' as const,
          recommendations: [],
        };
      }
      if (currentNs) {
        if (line.includes('Deployments:')) {
          currentNs.deploymentsCount = parseInt(line.match(/\d+/)?.[0] || '0');
        }
        if (line.includes('Coverage:')) {
          const pct = line.match(/(\d+(?:\.\d+)?)/);
          currentNs.coveragePercentage = pct ? parseFloat(pct[1]) : 0;
        }
        if (line.includes('Risk:') || line.includes('Level:')) {
          if (line.toLowerCase().includes('high')) currentNs.riskLevel = 'high';
          else if (line.toLowerCase().includes('low')) currentNs.riskLevel = 'low';
          else currentNs.riskLevel = 'medium';
        }
      }
    }
    if (currentNs) namespaces.push(currentNs);
  } else if (typeof data === 'object') {
    // JSON response from analyze_cluster_availability
    if (data.summary) {
      metrics.totalDeployments = data.summary.totalDeployments || 0;
      metrics.totalPDBs = data.summary.deploymentsWithPDB || data.summary.totalPDBs || 0;
      metrics.totalPolicies = data.summary.totalPolicies || 0;
      metrics.healthyPods = data.summary.healthyPods || 0;
      metrics.totalPods = data.summary.totalPods || 0;
    }
    if (data.coverage) {
      metrics.totalPDBs = data.coverage.covered || metrics.totalPDBs;
    }
    if (data.namespaces && Array.isArray(data.namespaces)) {
      namespaces = data.namespaces.map((ns: any) => {
        // Handle deployments as array or count
        const deploymentsCount = Array.isArray(ns.deployments)
          ? ns.deployments.length
          : (ns.deploymentsCount || 0);

        // Handle coverage as object or number
        const coveragePercentage = typeof ns.coverage === 'object'
          ? (ns.coverage.percentage || 0)
          : (ns.coveragePercentage || ns.coverage || 0);

        // Calculate PDBs count from deployments if available
        const pdbsCount = Array.isArray(ns.deployments)
          ? ns.deployments.filter((d: any) => d.hasPDB).length
          : (ns.pdbsCount || 0);

        // Determine risk level based on coverage
        let riskLevel: 'low' | 'medium' | 'high' = 'medium';
        if (coveragePercentage >= 80) riskLevel = 'low';
        else if (coveragePercentage < 50) riskLevel = 'high';

        return {
          namespace: ns.name || ns.namespace,
          podsCount: ns.pods || ns.podsCount || 0,
          deploymentsCount,
          pdbsCount,
          policiesCount: ns.policies || ns.policiesCount || 0,
          coveragePercentage,
          riskLevel: ns.risk || ns.riskLevel || riskLevel,
          recommendations: ns.recommendations || [],
        };
      });
    }
  }

  return { metrics, namespaces };
};

// Main Component
const ClusterAnalysis: React.FC = () => {
  const [namespace, setNamespace] = useState<string>('');

  // Load cluster analysis
  const { data: clusterData, isLoading, error, refetch } = useQuery({
    queryKey: ['clusterAnalysis'],
    queryFn: () => mcpClient.analyzeCluster(undefined, true),
    refetchInterval: 60000, // Refresh every minute
  });

  // Load workload patterns for additional data
  const { data: workloadData } = useQuery({
    queryKey: ['workloadPatterns'],
    queryFn: () => mcpClient.analyzeWorkloadPatterns(),
  });

  // Parse the data
  const { metrics, namespaces: namespaceAnalysis } = parseAnalysisData(clusterData);

  // Extract unique namespaces from analysis
  const availableNamespaces = namespaceAnalysis.map(ns => ns.namespace);

  // Chart data - use metrics or defaults
  const safeMetrics = metrics || {
    totalPods: 0,
    totalDeployments: 0,
    totalPDBs: 0,
    totalPolicies: 0,
    healthyPods: 0,
    unhealthyPods: 0,
    nodesCount: 0,
    lastUpdated: new Date(),
  };

  const coverageData = [
    { name: 'Covered', value: safeMetrics.totalPDBs || 0, color: chartColors.success },
    { name: 'Uncovered', value: Math.max(0, (safeMetrics.totalDeployments || 0) - (safeMetrics.totalPDBs || 0)), color: chartColors.error },
  ];

  const healthData = [
    { name: 'Healthy', value: safeMetrics.healthyPods || safeMetrics.totalPods || 0, color: chartColors.success },
    { name: 'Unhealthy', value: safeMetrics.unhealthyPods || 0, color: chartColors.error },
  ];

  const filteredNamespaces = namespace
    ? namespaceAnalysis.filter((ns) => ns.namespace === namespace)
    : namespaceAnalysis;

  return (
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
          Insights
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="h3">
            Cluster Analysis
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            disabled={isLoading}
            size="small"
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load cluster analysis: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
      )}

      {/* Loading */}
      {isLoading && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 4 }}>
          {[1, 2, 3, 4].map(i => (
            <Skeleton key={i} variant="rounded" height={100} sx={{ borderRadius: 3 }} />
          ))}
        </Box>
      )}

      {/* Stats */}
      {!isLoading && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 5 }}>
          <StatCard
            title="Total Deployments"
            value={safeMetrics.totalDeployments}
            icon={<StorageIcon />}
          />
          <StatCard
            title="Total Pods"
            value={safeMetrics.totalPods}
            icon={<MemoryIcon />}
            subtitle={`${safeMetrics.healthyPods} healthy`}
          />
          <StatCard
            title="PDBs Active"
            value={safeMetrics.totalPDBs}
            icon={<ShieldIcon />}
            color={chartColors.success}
          />
          <StatCard
            title="Policies"
            value={safeMetrics.totalPolicies}
            icon={<TrendingUpIcon />}
            color={chartColors.primary}
          />
        </Box>
      )}

      {/* Charts */}
      {!isLoading && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 5 }}>
          {/* Coverage Chart */}
          <Box
            sx={{
              p: 3,
              borderRadius: 3,
              bgcolor: 'background.paper',
              border: 1,
              borderColor: 'divider',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              PDB Coverage
            </Typography>
            <Box sx={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={coverageData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {coverageData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, mt: 1 }}>
              {coverageData.map((item) => (
                <Box key={item.name} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: item.color }} />
                  <Typography variant="caption">
                    {item.name}: {item.value}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>

          {/* Health Chart */}
          <Box
            sx={{
              p: 3,
              borderRadius: 3,
              bgcolor: 'background.paper',
              border: 1,
              borderColor: 'divider',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              Pod Health
            </Typography>
            <Box sx={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={healthData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={80} />
                  <RechartsTooltip />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {healthData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Box>
        </Box>
      )}

      {/* Namespace Analysis */}
      {!isLoading && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h6">
              Namespace Analysis
            </Typography>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Filter by Namespace</InputLabel>
              <Select
                value={namespace}
                label="Filter by Namespace"
                onChange={(e) => setNamespace(e.target.value)}
              >
                <MenuItem value="">All Namespaces</MenuItem>
                {availableNamespaces.map((ns: string) => (
                  <MenuItem key={ns} value={ns}>{ns}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {filteredNamespaces.length > 0 ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {filteredNamespaces.map((ns) => (
                <NamespaceRow key={ns.namespace} ns={ns} />
              ))}
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No namespace data available
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Make sure the cluster is connected and has workloads deployed.
              </Typography>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

export default ClusterAnalysis;
