import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Alert,
  Tabs,
  Tab,
  Tooltip,
  Skeleton,
  alpha,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
  KeyboardArrowRight as ArrowRightIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { useNotificationStore } from '@/store';
import mcpClient from '@/api/mcp';
import { AvailabilityPolicy } from '@/types';

// Policy Card
const PolicyCard: React.FC<{
  policy: AvailabilityPolicy;
  onEdit: () => void;
  onDelete: () => void;
}> = ({ policy, onEdit, onDelete }) => {
  const statusColors: Record<string, 'success' | 'warning' | 'error'> = {
    active: 'success',
    inactive: 'warning',
    draft: 'error',
  };

  return (
    <Box
      sx={{
        p: 2.5,
        borderRadius: 3,
        bgcolor: 'background.paper',
        border: 1,
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        transition: 'all 0.15s ease',
        '&:hover': {
          borderColor: 'primary.main',
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="body1" fontWeight={600}>
            {policy.name}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {policy.description || 'No description'}
          </Typography>
        </Box>
        <Chip
          label={policy.status}
          size="small"
          color={statusColors[policy.status] || 'default'}
        />
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Chip
          label={`Priority: ${policy.priority}`}
          size="small"
          variant="outlined"
        />
        <Chip
          label={policy.enforcement}
          size="small"
          variant="outlined"
        />
        {policy.namespace && (
          <Chip
            label={`ns: ${policy.namespace}`}
            size="small"
            variant="outlined"
          />
        )}
      </Box>

      <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
        <Button size="small" startIcon={<EditIcon />} onClick={onEdit}>
          Edit
        </Button>
        <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={onDelete}>
          Delete
        </Button>
      </Box>
    </Box>
  );
};

// Policy Form Dialog
const PolicyFormDialog: React.FC<{
  open: boolean;
  onClose: () => void;
  policy?: AvailabilityPolicy;
  onSave: (data: any) => void;
  isLoading: boolean;
}> = ({ open, onClose, policy, onSave, isLoading }) => {
  const [formData, setFormData] = useState({
    name: policy?.name || '',
    description: policy?.description || '',
    namespace: policy?.namespace || '',
    enforcement: policy?.enforcement || 'advisory',
    priority: policy?.priority || 0,
    status: policy?.status || 'draft',
  });

  const handleSubmit = () => {
    onSave(formData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6">
            {policy ? 'Edit Policy' : 'Create Policy'}
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, py: 1 }}>
          <TextField
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            size="small"
          />

          <TextField
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            multiline
            rows={2}
            size="small"
          />

          <TextField
            label="Namespace"
            value={formData.namespace}
            onChange={(e) => setFormData({ ...formData, namespace: e.target.value })}
            placeholder="Leave empty for all namespaces"
            size="small"
          />

          <FormControl size="small">
            <InputLabel>Enforcement</InputLabel>
            <Select
              value={formData.enforcement}
              label="Enforcement"
              onChange={(e) => setFormData({ ...formData, enforcement: e.target.value as any })}
            >
              <MenuItem value="strict">Strict</MenuItem>
              <MenuItem value="flexible">Flexible</MenuItem>
              <MenuItem value="advisory">Advisory</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Priority"
            type="number"
            value={formData.priority}
            onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
            size="small"
          />

          <FormControl size="small">
            <InputLabel>Status</InputLabel>
            <Select
              value={formData.status}
              label="Status"
              onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
            >
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
              <MenuItem value="draft">Draft</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!formData.name || isLoading}
        >
          {isLoading ? 'Saving...' : policy ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Main Component
const PolicyManager: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<AvailabilityPolicy | undefined>();
  const [deletePolicy, setDeletePolicy] = useState<AvailabilityPolicy | null>(null);

  const queryClient = useQueryClient();
  const { addNotification } = useNotificationStore();

  // Load policies
  const { data: policies, isLoading, error, refetch } = useQuery({
    queryKey: ['policies'],
    queryFn: () => mcpClient.listPolicies(),
  });

  // Create/Update policy
  const saveMutation = useMutation({
    mutationFn: (data: any) => {
      if (editingPolicy) {
        return mcpClient.updatePolicy(editingPolicy.id, data);
      }
      return mcpClient.createPolicy(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['policies']);
      setDialogOpen(false);
      setEditingPolicy(undefined);
      addNotification({
        type: 'success',
        title: editingPolicy ? 'Policy updated' : 'Policy created',
      });
    },
    onError: (err: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to save policy',
        message: err.message,
      });
    },
  });

  // Delete policy
  const deleteMutation = useMutation({
    mutationFn: (id: string) => mcpClient.deletePolicy(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['policies']);
      setDeletePolicy(null);
      addNotification({
        type: 'success',
        title: 'Policy deleted',
      });
    },
    onError: (err: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to delete policy',
        message: err.message,
      });
    },
  });

  const handleEdit = (policy: AvailabilityPolicy) => {
    setEditingPolicy(policy);
    setDialogOpen(true);
  };

  const handleCreate = () => {
    setEditingPolicy(undefined);
    setDialogOpen(true);
  };

  const activePolicies = policies?.filter((p: AvailabilityPolicy) => p.status === 'active') || [];
  const draftPolicies = policies?.filter((p: AvailabilityPolicy) => p.status !== 'active') || [];

  return (
    <Box sx={{ p: 4, maxWidth: 1400, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
          Configuration
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="h3">
            Policies
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => refetch()}
              disabled={isLoading}
              size="small"
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreate}
              size="small"
            >
              Create Policy
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Stats */}
      <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
        <Box
          sx={{
            px: 3,
            py: 2,
            borderRadius: 2,
            bgcolor: 'background.paper',
            border: 1,
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
          }}
        >
          <CheckCircleIcon color="success" />
          <Box>
            <Typography variant="h5">{activePolicies.length}</Typography>
            <Typography variant="caption" color="text.secondary">Active</Typography>
          </Box>
        </Box>
        <Box
          sx={{
            px: 3,
            py: 2,
            borderRadius: 2,
            bgcolor: 'background.paper',
            border: 1,
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
          }}
        >
          <WarningIcon color="warning" />
          <Box>
            <Typography variant="h5">{draftPolicies.length}</Typography>
            <Typography variant="caption" color="text.secondary">Draft/Inactive</Typography>
          </Box>
        </Box>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label={`Active (${activePolicies.length})`} />
          <Tab label={`Drafts (${draftPolicies.length})`} />
        </Tabs>
      </Box>

      {/* Loading */}
      {isLoading && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 2 }}>
          {[1, 2, 3].map(i => (
            <Skeleton key={i} variant="rounded" height={160} sx={{ borderRadius: 3 }} />
          ))}
        </Box>
      )}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load policies: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
      )}

      {/* Active Policies Tab */}
      {tabValue === 0 && !isLoading && (
        activePolicies.length > 0 ? (
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 2 }}>
            {activePolicies.map((policy: AvailabilityPolicy) => (
              <PolicyCard
                key={policy.id}
                policy={policy}
                onEdit={() => handleEdit(policy)}
                onDelete={() => setDeletePolicy(policy)}
              />
            ))}
          </Box>
        ) : (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No active policies
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Create a policy to manage PDB availability.
            </Typography>
            <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
              Create Policy
            </Button>
          </Box>
        )
      )}

      {/* Drafts Tab */}
      {tabValue === 1 && !isLoading && (
        draftPolicies.length > 0 ? (
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 2 }}>
            {draftPolicies.map((policy: AvailabilityPolicy) => (
              <PolicyCard
                key={policy.id}
                policy={policy}
                onEdit={() => handleEdit(policy)}
                onDelete={() => setDeletePolicy(policy)}
              />
            ))}
          </Box>
        ) : (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h6" color="text.secondary">
              No draft policies
            </Typography>
          </Box>
        )
      )}

      {/* Create/Edit Dialog */}
      <PolicyFormDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setEditingPolicy(undefined);
        }}
        policy={editingPolicy}
        onSave={(data) => saveMutation.mutate(data)}
        isLoading={saveMutation.isLoading}
      />

      {/* Delete Confirmation */}
      <Dialog open={!!deletePolicy} onClose={() => setDeletePolicy(null)}>
        <DialogTitle>Delete Policy</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{deletePolicy?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeletePolicy(null)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => deletePolicy && deleteMutation.mutate(deletePolicy.id)}
            disabled={deleteMutation.isLoading}
          >
            {deleteMutation.isLoading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PolicyManager;
