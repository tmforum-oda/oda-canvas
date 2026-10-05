import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  IconButton,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Collapse,
  alpha,
  Tooltip,
} from '@mui/material';
import {
  Send as SendIcon,
  Settings as SettingsIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

import {
  useChatStore,
  useAppStore,
  useToolStore,
  useNotificationStore
} from '@/store';
import { createAIClient } from '@/api/ai';
import mcpClient from '@/api/mcp';
import { ChatMessage, ToolCall, AIProvider } from '@/types';

// AI Provider configurations
const providers: { value: AIProvider; label: string }[] = [
  { value: 'claude', label: 'Claude' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'azure-openai', label: 'Azure OpenAI' },
  { value: 'gemini', label: 'Gemini' },
];

// Tool Call Display
const ToolCallDisplay: React.FC<{ toolCall: ToolCall }> = ({ toolCall }) => {
  const [expanded, setExpanded] = useState(false);
  const theme = useAppStore((state) => state.theme);

  return (
    <Box
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        overflow: 'hidden',
        my: 1,
      }}
    >
      <Box
        onClick={() => setExpanded(!expanded)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          p: 1.5,
          cursor: 'pointer',
          bgcolor: (t) => alpha(t.palette.text.primary, 0.02),
          '&:hover': {
            bgcolor: (t) => alpha(t.palette.text.primary, 0.04),
          },
        }}
      >
        <Box
          sx={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            bgcolor:
              toolCall.status === 'completed' ? 'success.main' :
              toolCall.status === 'error' ? 'error.main' :
              'warning.main',
          }}
        />
        <Typography variant="body2" fontWeight={600} sx={{ flex: 1 }}>
          {toolCall.name}
        </Typography>
        <Chip
          label={toolCall.status}
          size="small"
          color={
            toolCall.status === 'completed' ? 'success' :
            toolCall.status === 'error' ? 'error' :
            'warning'
          }
          sx={{ height: 20, fontSize: '0.6875rem' }}
        />
        {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          {Object.keys(toolCall.parameters).length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                Parameters
              </Typography>
              <Box
                sx={{
                  borderRadius: 1,
                  overflow: 'hidden',
                  '& pre': { m: '0 !important', fontSize: '0.75rem !important' },
                }}
              >
                <SyntaxHighlighter
                  language="json"
                  style={theme === 'dark' ? oneDark : oneLight}
                  customStyle={{ margin: 0, padding: 8 }}
                >
                  {JSON.stringify(toolCall.parameters, null, 2)}
                </SyntaxHighlighter>
              </Box>
            </Box>
          )}

          {toolCall.result && (
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                Result
              </Typography>
              <Box
                sx={{
                  borderRadius: 1,
                  overflow: 'hidden',
                  maxHeight: 200,
                  '& pre': { m: '0 !important', fontSize: '0.75rem !important' },
                }}
              >
                <SyntaxHighlighter
                  language="json"
                  style={theme === 'dark' ? oneDark : oneLight}
                  customStyle={{ margin: 0, padding: 8, maxHeight: 200, overflow: 'auto' }}
                >
                  {typeof toolCall.result === 'string'
                    ? toolCall.result
                    : JSON.stringify(toolCall.result, null, 2)}
                </SyntaxHighlighter>
              </Box>
            </Box>
          )}

          {toolCall.error && (
            <Typography variant="body2" color="error">
              {toolCall.error}
            </Typography>
          )}
        </Box>
      </Collapse>
    </Box>
  );
};

// Message Component
const Message: React.FC<{ message: ChatMessage }> = ({ message }) => {
  const theme = useAppStore((state) => state.theme);
  const isUser = message.role === 'user';

  return (
    <Box
      sx={{
        display: 'flex',
        gap: 2,
        py: 2.5,
        px: 3,
        bgcolor: isUser ? 'transparent' : (t) => alpha(t.palette.text.primary, 0.02),
      }}
    >
      <Box
        sx={{
          width: 32,
          height: 32,
          borderRadius: 2,
          bgcolor: isUser ? 'primary.main' : 'text.secondary',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          color: isUser ? 'primary.contrastText' : 'background.paper',
        }}
      >
        {isUser ? <PersonIcon sx={{ fontSize: 18 }} /> : <BotIcon sx={{ fontSize: 18 }} />}
      </Box>

      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
          {isUser ? 'You' : 'Assistant'} · {message.timestamp.toLocaleTimeString()}
        </Typography>

        <Box
          sx={{
            '& p': { m: 0, mb: 1.5, '&:last-child': { mb: 0 } },
            '& pre': {
              borderRadius: 2,
              overflow: 'hidden',
              m: '0 !important',
              my: '12px !important',
            },
            '& code': {
              fontSize: '0.8125rem',
              fontFamily: '"JetBrains Mono", "Fira Code", monospace',
            },
            '& ul, & ol': { pl: 2.5, my: 1 },
            '& li': { mb: 0.5 },
          }}
        >
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={theme === 'dark' ? oneDark : oneLight}
                    language={match[1]}
                    PreTag="div"
                    customStyle={{ margin: 0, borderRadius: 8 }}
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code
                    className={className}
                    style={{
                      backgroundColor: theme === 'dark' ? '#1E293B' : '#F1F5F9',
                      padding: '2px 6px',
                      borderRadius: 4,
                    }}
                    {...props}
                  >
                    {children}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </Box>

        {message.toolCalls && message.toolCalls.length > 0 && (
          <Box sx={{ mt: 2 }}>
            {message.toolCalls.map((tc) => (
              <ToolCallDisplay key={tc.id} toolCall={tc} />
            ))}
          </Box>
        )}
      </Box>
    </Box>
  );
};

// Main Component
const ChatInterface: React.FC = () => {
  const [input, setInput] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { aiConfig, setAIConfig } = useAppStore();
  const {
    messages,
    isLoading,
    error,
    addMessage,
    clearMessages,
    setLoading,
    setError
  } = useChatStore();
  const { availableTools } = useToolStore();
  const { addNotification } = useNotificationStore();

  // Load available tools
  const { data: tools } = useQuery({
    queryKey: ['tools'],
    queryFn: () => mcpClient.listTools(),
    refetchOnMount: true,
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Omit<ChatMessage, 'id' | 'timestamp'> = {
      role: 'user',
      content: input.trim(),
    };

    addMessage(userMessage);
    setInput('');
    setLoading(true);
    setError(undefined);

    try {
      const aiClient = createAIClient(aiConfig);
      const currentMessages = [...messages, {
        ...userMessage,
        id: crypto.randomUUID(),
        timestamp: new Date(),
      }];

      const shouldUseTools = tools && tools.length > 0;

      let response;
      if (shouldUseTools) {
        response = await aiClient.chatWithTools(currentMessages, tools);
      } else {
        response = await aiClient.chat(currentMessages);
      }

      addMessage({
        role: 'assistant',
        content: response.message.content,
        toolCalls: response.message.toolCalls,
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);

      addMessage({
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request.',
        error: errorMessage,
      });

      addNotification({
        type: 'error',
        title: 'Failed to send message',
        message: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <Box
        sx={{
          p: 3,
          pb: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box>
          <Typography variant="overline" color="text.secondary" sx={{ display: 'block' }}>
            AI Assistant
          </Typography>
          <Typography variant="h5">Chat</Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Settings">
            <IconButton onClick={() => setShowSettings(!showSettings)}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Clear chat">
            <IconButton onClick={clearMessages} disabled={messages.length === 0}>
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Settings Panel */}
      <Collapse in={showSettings}>
        <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider', bgcolor: (t) => alpha(t.palette.text.primary, 0.02) }}>
          <Typography variant="body2" fontWeight={600} sx={{ mb: 2 }}>
            AI Configuration
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Provider</InputLabel>
              <Select
                value={aiConfig.provider}
                label="Provider"
                onChange={(e) => setAIConfig({ ...aiConfig, provider: e.target.value as AIProvider })}
              >
                {providers.map((p) => (
                  <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              size="small"
              label="API Key"
              type="password"
              value={aiConfig.apiKey || ''}
              onChange={(e) => setAIConfig({ ...aiConfig, apiKey: e.target.value })}
              placeholder="sk-..."
              sx={{ minWidth: 200 }}
            />
            <TextField
              size="small"
              label="Model"
              value={aiConfig.model || ''}
              onChange={(e) => setAIConfig({ ...aiConfig, model: e.target.value })}
              placeholder="e.g., claude-3-opus"
              sx={{ minWidth: 180 }}
            />
          </Box>
        </Box>
      </Collapse>

      {/* Messages */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {messages.length === 0 ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', p: 4 }}>
            <Box sx={{ textAlign: 'center', maxWidth: 400 }}>
              <Box
                sx={{
                  width: 56,
                  height: 56,
                  borderRadius: 3,
                  bgcolor: 'primary.main',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <BotIcon sx={{ color: 'primary.contrastText', fontSize: 28 }} />
              </Box>
              <Typography variant="h6" gutterBottom>
                PDB Management Assistant
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Ask me about managing Pod Disruption Budgets, creating availability policies, or analyzing your cluster.
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {[
                  'List all PDBs in the default namespace',
                  'Analyze my cluster\'s PDB coverage',
                  'Create a policy for high availability'
                ].map((suggestion) => (
                  <Chip
                    key={suggestion}
                    label={suggestion}
                    variant="outlined"
                    onClick={() => setInput(suggestion)}
                    sx={{ cursor: 'pointer' }}
                  />
                ))}
              </Box>
            </Box>
          </Box>
        ) : (
          <Box>
            {messages.map((message) => (
              <Message key={message.id} message={message} />
            ))}
            {isLoading && (
              <Box sx={{ display: 'flex', gap: 2, py: 2.5, px: 3 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: 2,
                    bgcolor: 'text.secondary',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <CircularProgress size={16} sx={{ color: 'background.paper' }} />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ alignSelf: 'center' }}>
                  Thinking...
                </Typography>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Box>
        )}
      </Box>

      {/* Input */}
      <Box sx={{ p: 3, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 2, maxWidth: 900, mx: 'auto' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={isLoading}
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: 'background.paper',
              },
            }}
          />
          <Button
            variant="contained"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            sx={{ minWidth: 100 }}
          >
            {isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          </Button>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 1 }}>
          Press Enter to send · Shift+Enter for new line
        </Typography>
      </Box>
    </Box>
  );
};

export default ChatInterface;
