import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
  InputAdornment,
  Tooltip,
  Skeleton,
  Tabs,
  Tab,
  alpha,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
} from '@mui/material';
import {
  Search as SearchIcon,
  PlayArrow as PlayIcon,
  Close as CloseIcon,
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  AccessTime as AccessTimeIcon,
  KeyboardArrowRight as ArrowRightIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

import { useToolStore, useNotificationStore, useAppStore } from '@/store';
import mcpClient from '@/api/mcp';
import { MCPTool, ToolExecution } from '@/types';

// Parameter Input Component
const ParameterInput: React.FC<{
  name: string;
  schema: any;
  value: any;
  onChange: (value: any) => void;
  error?: string;
}> = ({ name, schema, value, onChange, error }) => {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const newValue = event.target.value;

    if (schema.type === 'number' || schema.type === 'integer') {
      onChange(newValue === '' ? undefined : Number(newValue));
    } else if (schema.type === 'array') {
      try {
        onChange(JSON.parse(newValue));
      } catch {
        onChange(newValue.split(',').map((s: string) => s.trim()).filter((s: string) => s));
      }
    } else if (schema.type === 'object') {
      try {
        onChange(JSON.parse(newValue));
      } catch {
        onChange(newValue);
      }
    } else {
      onChange(newValue);
    }
  };

  const getDisplayValue = () => {
    if (value === undefined || value === null) return '';
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  };

  if (schema.type === 'boolean') {
    return (
      <FormControl fullWidth error={!!error} size="small">
        <InputLabel>{name}</InputLabel>
        <Select
          value={value === undefined ? '' : String(value)}
          label={name}
          onChange={(e) => onChange(e.target.value === 'true')}
        >
          <MenuItem value=""><em>Not set</em></MenuItem>
          <MenuItem value="true">true</MenuItem>
          <MenuItem value="false">false</MenuItem>
        </Select>
        {(error || schema.description) && (
          <FormHelperText>{error || schema.description}</FormHelperText>
        )}
      </FormControl>
    );
  }

  const isMultiline = schema.type === 'array' || schema.type === 'object';

  return (
    <TextField
      fullWidth
      size="small"
      label={name}
      value={getDisplayValue()}
      onChange={handleChange}
      type={schema.type === 'number' || schema.type === 'integer' ? 'number' : 'text'}
      multiline={isMultiline}
      rows={isMultiline ? 3 : 1}
      error={!!error}
      helperText={error || schema.description}
      placeholder={
        schema.type === 'array' ? 'Comma-separated or JSON array' :
        schema.type === 'object' ? 'JSON object' :
        schema.example || ''
      }
    />
  );
};

// Tool Execution Dialog
const ToolDialog: React.FC<{
  tool: MCPTool | null;
  open: boolean;
  onClose: () => void;
  onExecute: (toolName: string, parameters: Record<string, any>) => void;
  isExecuting: boolean;
  lastResult?: ToolExecution;
}> = ({ tool, open, onClose, onExecute, isExecuting, lastResult }) => {
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showResult, setShowResult] = useState(false);
  const theme = useAppStore((state) => state.theme);

  useEffect(() => {
    if (tool) {
      const defaultParams: Record<string, any> = {};
      if (tool.parameters?.properties) {
        Object.entries(tool.parameters.properties).forEach(([key, schema]: [string, any]) => {
          if (schema.default !== undefined) {
            defaultParams[key] = schema.default;
          }
        });
      }
      setParameters(defaultParams);
      setErrors({});
      setShowResult(false);
    }
  }, [tool]);

  useEffect(() => {
    if (lastResult && !lastResult.error) {
      setShowResult(true);
    }
  }, [lastResult]);

  const validateParameters = () => {
    const newErrors: Record<string, string> = {};
    if (tool?.required) {
      tool.required.forEach(param => {
        if (parameters[param] === undefined || parameters[param] === '') {
          newErrors[param] = 'Required';
        }
      });
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleExecute = () => {
    if (!tool || !validateParameters()) return;
    setShowResult(false);
    onExecute(tool.name, parameters);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (!tool) return null;

  const hasParams = tool.parameters?.properties && Object.keys(tool.parameters.properties).length > 0;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { maxHeight: '85vh' } }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6" component="span">{tool.name}</Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          {tool.description}
        </Typography>
      </DialogTitle>

      <DialogContent dividers sx={{ py: 3 }}>
        {/* Parameters */}
        {hasParams && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="overline" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
              Parameters
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {Object.entries(tool.parameters!.properties).map(([name, schema]: [string, any]) => (
                <ParameterInput
                  key={name}
                  name={name}
                  schema={schema}
                  value={parameters[name]}
                  onChange={(value) => {
                    setParameters(prev => ({ ...prev, [name]: value }));
                    if (errors[name]) setErrors(prev => ({ ...prev, [name]: '' }));
                  }}
                  error={errors[name]}
                />
              ))}
            </Box>
          </Box>
        )}

        {!hasParams && (
          <Alert severity="info" sx={{ mb: 3 }}>
            This tool doesn't require any parameters.
          </Alert>
        )}

        {/* Loading State */}
        {isExecuting && (
          <Box sx={{ mb: 3 }}>
            <LinearProgress sx={{ mb: 1 }} />
            <Typography variant="body2" color="text.secondary">
              Executing...
            </Typography>
          </Box>
        )}

        {/* Result */}
        {showResult && lastResult && (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="overline" color="text.secondary">
                Result {lastResult.duration && `(${lastResult.duration}ms)`}
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                <Tooltip title="Copy">
                  <IconButton
                    size="small"
                    onClick={() => handleCopy(JSON.stringify(lastResult.result, null, 2))}
                  >
                    <CopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            {lastResult.error ? (
              <Alert severity="error">{lastResult.error}</Alert>
            ) : (
              <Box
                sx={{
                  borderRadius: 2,
                  overflow: 'hidden',
                  border: 1,
                  borderColor: 'divider',
                  '& pre': { m: '0 !important', fontSize: '0.8125rem !important' },
                }}
              >
                <SyntaxHighlighter
                  language="json"
                  style={theme === 'dark' ? oneDark : oneLight}
                  customStyle={{
                    margin: 0,
                    padding: 16,
                    maxHeight: 300,
                    overflow: 'auto',
                  }}
                >
                  {typeof lastResult.result === 'string'
                    ? lastResult.result
                    : JSON.stringify(lastResult.result, null, 2)}
                </SyntaxHighlighter>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Close
        </Button>
        <Button
          variant="contained"
          onClick={handleExecute}
          disabled={isExecuting}
          startIcon={<PlayIcon />}
        >
          {isExecuting ? 'Running...' : 'Execute'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Tool Card
const ToolCard: React.FC<{
  tool: MCPTool;
  onClick: () => void;
  lastExecution?: ToolExecution;
}> = ({ tool, onClick, lastExecution }) => {
  const paramCount = tool.parameters?.properties ? Object.keys(tool.parameters.properties).length : 0;
  const requiredCount = tool.required?.length || 0;

  return (
    <Box
      onClick={onClick}
      sx={{
        p: 2.5,
        borderRadius: 3,
        bgcolor: 'background.paper',
        border: 1,
        borderColor: 'divider',
        cursor: 'pointer',
        transition: 'all 0.15s ease',
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
        '&:hover': {
          borderColor: 'primary.main',
          bgcolor: (theme) => alpha(theme.palette.primary.main, 0.02),
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 1 }}>
        <Typography variant="body1" fontWeight={600} sx={{ flex: 1 }}>
          {tool.name}
        </Typography>
        {lastExecution && (
          <Chip
            icon={
              lastExecution.error ? <ErrorIcon /> :
              lastExecution.endTime ? <CheckCircleIcon /> :
              <AccessTimeIcon />
            }
            label={
              lastExecution.error ? 'Error' :
              lastExecution.endTime ? 'OK' :
              '...'
            }
            size="small"
            color={
              lastExecution.error ? 'error' :
              lastExecution.endTime ? 'success' :
              'warning'
            }
            sx={{ height: 24, '& .MuiChip-icon': { fontSize: 14 } }}
          />
        )}
      </Box>

      <Typography
        variant="body2"
        color="text.secondary"
        sx={{
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
          lineHeight: 1.5,
          minHeight: 42,
        }}
      >
        {tool.description}
      </Typography>

      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip label={`${paramCount} params`} size="small" variant="outlined" />
          {requiredCount > 0 && (
            <Chip label={`${requiredCount} required`} size="small" color="warning" variant="outlined" />
          )}
        </Box>
        <ArrowRightIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
      </Box>
    </Box>
  );
};

// Execution History Item
const HistoryItem: React.FC<{
  execution: ToolExecution;
  onClick: () => void;
}> = ({ execution, onClick }) => {
  return (
    <Box
      onClick={onClick}
      sx={{
        p: 2,
        borderRadius: 2,
        border: 1,
        borderColor: 'divider',
        cursor: 'pointer',
        transition: 'all 0.15s ease',
        '&:hover': {
          bgcolor: (theme) => alpha(theme.palette.text.primary, 0.02),
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box
          sx={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            bgcolor: execution.error ? 'error.main' : 'success.main',
            flexShrink: 0,
          }}
        />
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="body2" fontWeight={600} noWrap>
            {execution.toolName}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {execution.startTime.toLocaleString()}
            {execution.duration && ` · ${execution.duration}ms`}
          </Typography>
        </Box>
        <ArrowRightIcon sx={{ color: 'text.secondary', fontSize: 18 }} />
      </Box>
    </Box>
  );
};

// Main Component
const ToolExplorer: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<ToolExecution | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [lastResult, setLastResult] = useState<ToolExecution | undefined>();
  const theme = useAppStore((state) => state.theme);

  const {
    availableTools,
    toolHistory,
    setAvailableTools,
    setExecutingTool,
    addToolExecution,
    updateToolExecution
  } = useToolStore();
  const { addNotification } = useNotificationStore();

  // Load tools via serverInfo (same as Dashboard)
  const { data: serverInfo, isLoading, error, refetch } = useQuery({
    queryKey: ['serverInfo'],
    queryFn: () => mcpClient.getServerInfo(),
  });

  // Extract tools from server info
  const tools = serverInfo?.tools || [];

  // Update store when tools are loaded
  useEffect(() => {
    if (tools.length > 0) {
      setAvailableTools(tools);
    }
  }, [tools, setAvailableTools]);

  // Execute tool
  const executeMutation = useMutation({
    mutationFn: ({ toolName, parameters }: { toolName: string; parameters: Record<string, any> }) =>
      mcpClient.executeTool(toolName, parameters),
    onMutate: ({ toolName, parameters }) => {
      setExecutingTool(toolName);
      addToolExecution({ toolName, parameters, startTime: new Date() });
    },
    onSuccess: (result) => {
      updateToolExecution(result.id, {
        result: result.result,
        endTime: result.endTime,
        duration: result.duration,
      });
      setLastResult(result);
      addNotification({
        type: 'success',
        title: 'Tool executed',
        message: `${result.toolName} completed in ${result.duration}ms`,
      });
    },
    onError: (error: any, { toolName }) => {
      const errorMessage = error instanceof Error ? error.message : 'Execution failed';
      const latestExecution = toolHistory.find(exec => exec.toolName === toolName && !exec.endTime);
      if (latestExecution) {
        updateToolExecution(latestExecution.id, {
          error: errorMessage,
          endTime: new Date(),
          duration: Date.now() - latestExecution.startTime.getTime(),
        });
      }
      addNotification({
        type: 'error',
        title: 'Execution failed',
        message: errorMessage,
      });
    },
    onSettled: () => setExecutingTool(undefined),
  });

  // Use tools from query data, falling back to store
  const displayTools = tools.length > 0 ? tools : availableTools;

  // Filter tools
  const filteredTools = useMemo(() => {
    if (!searchFilter) return displayTools;
    const lower = searchFilter.toLowerCase();
    return displayTools.filter(
      tool =>
        tool.name.toLowerCase().includes(lower) ||
        tool.description.toLowerCase().includes(lower)
    );
  }, [displayTools, searchFilter]);

  const getRecentExecution = (toolName: string) => {
    return toolHistory.find(exec => exec.toolName === toolName);
  };

  const handleDownloadHistory = () => {
    const data = toolHistory.map(exec => ({
      tool: exec.toolName,
      parameters: exec.parameters,
      result: exec.result,
      error: exec.error,
      duration: exec.duration,
      timestamp: exec.startTime.toISOString(),
    }));
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tool-history-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
          MCP Tools
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="h3">
            Tool Explorer
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

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label={`Tools (${displayTools.length})`} />
          <Tab label={`History (${toolHistory.length})`} />
        </Tabs>
      </Box>

      {/* Tools Tab */}
      {tabValue === 0 && (
        <>
          {/* Search */}
          <TextField
            fullWidth
            placeholder="Search tools..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            size="small"
            sx={{ mb: 3, maxWidth: 400 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: 'text.secondary' }} />
                </InputAdornment>
              ),
            }}
          />

          {/* Loading */}
          {isLoading && (
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 2 }}>
              {[1, 2, 3, 4, 5, 6].map(i => (
                <Skeleton key={i} variant="rounded" height={140} sx={{ borderRadius: 3 }} />
              ))}
            </Box>
          )}

          {/* Error */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              Failed to load tools: {error instanceof Error ? error.message : 'Unknown error'}
            </Alert>
          )}

          {/* Tools Grid */}
          {!isLoading && filteredTools.length > 0 && (
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 2 }}>
              {filteredTools.map(tool => (
                <ToolCard
                  key={tool.name}
                  tool={tool}
                  onClick={() => {
                    setSelectedTool(tool);
                    setLastResult(undefined);
                  }}
                  lastExecution={getRecentExecution(tool.name)}
                />
              ))}
            </Box>
          )}

          {/* Empty State */}
          {!isLoading && filteredTools.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchFilter ? 'No tools match your search' : 'No tools available'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {searchFilter
                  ? 'Try different keywords'
                  : 'Make sure the MCP server is connected.'}
              </Typography>
            </Box>
          )}
        </>
      )}

      {/* History Tab */}
      {tabValue === 1 && (
        <>
          {toolHistory.length > 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
              <Button
                size="small"
                startIcon={<DownloadIcon />}
                onClick={handleDownloadHistory}
              >
                Export
              </Button>
            </Box>
          )}

          {toolHistory.length > 0 ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {toolHistory.map(execution => (
                <HistoryItem
                  key={execution.id}
                  execution={execution}
                  onClick={() => setSelectedExecution(execution)}
                />
              ))}
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No execution history
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Execute some tools to see the history here.
              </Typography>
            </Box>
          )}
        </>
      )}

      {/* Tool Execution Dialog */}
      <ToolDialog
        tool={selectedTool}
        open={!!selectedTool}
        onClose={() => setSelectedTool(null)}
        onExecute={(toolName, parameters) => executeMutation.mutate({ toolName, parameters })}
        isExecuting={executeMutation.isLoading}
        lastResult={lastResult}
      />

      {/* Execution Details Dialog */}
      <Dialog
        open={!!selectedExecution}
        onClose={() => setSelectedExecution(null)}
        maxWidth="md"
        fullWidth
      >
        {selectedExecution && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6">{selectedExecution.toolName}</Typography>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  <IconButton
                    size="small"
                    onClick={() => {
                      const data = {
                        tool: selectedExecution.toolName,
                        parameters: selectedExecution.parameters,
                        result: selectedExecution.result,
                        error: selectedExecution.error,
                        duration: selectedExecution.duration,
                        timestamp: selectedExecution.startTime.toISOString(),
                      };
                      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `${selectedExecution.toolName}-${selectedExecution.id}.json`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    <DownloadIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => setSelectedExecution(null)}>
                    <CloseIcon />
                  </IconButton>
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              <Box sx={{ display: 'flex', gap: 3, mb: 3, flexWrap: 'wrap' }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Time</Typography>
                  <Typography variant="body2">{selectedExecution.startTime.toLocaleString()}</Typography>
                </Box>
                {selectedExecution.duration && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">Duration</Typography>
                    <Typography variant="body2">{selectedExecution.duration}ms</Typography>
                  </Box>
                )}
                <Box>
                  <Typography variant="caption" color="text.secondary">Status</Typography>
                  <Typography variant="body2">
                    {selectedExecution.error ? 'Failed' : 'Success'}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                  Parameters
                </Typography>
                <Box
                  sx={{
                    borderRadius: 2,
                    overflow: 'hidden',
                    border: 1,
                    borderColor: 'divider',
                    '& pre': { m: '0 !important', fontSize: '0.8125rem !important' },
                  }}
                >
                  <SyntaxHighlighter
                    language="json"
                    style={theme === 'dark' ? oneDark : oneLight}
                    customStyle={{ margin: 0, padding: 16 }}
                  >
                    {JSON.stringify(selectedExecution.parameters, null, 2)}
                  </SyntaxHighlighter>
                </Box>
              </Box>

              {selectedExecution.result && (
                <Box>
                  <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                    Result
                  </Typography>
                  <Box
                    sx={{
                      borderRadius: 2,
                      overflow: 'hidden',
                      border: 1,
                      borderColor: 'divider',
                      '& pre': { m: '0 !important', fontSize: '0.8125rem !important' },
                    }}
                  >
                    <SyntaxHighlighter
                      language="json"
                      style={theme === 'dark' ? oneDark : oneLight}
                      customStyle={{ margin: 0, padding: 16, maxHeight: 300, overflow: 'auto' }}
                    >
                      {typeof selectedExecution.result === 'string'
                        ? selectedExecution.result
                        : JSON.stringify(selectedExecution.result, null, 2)}
                    </SyntaxHighlighter>
                  </Box>
                </Box>
              )}

              {selectedExecution.error && (
                <Alert severity="error">{selectedExecution.error}</Alert>
              )}
            </DialogContent>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default ToolExplorer;
