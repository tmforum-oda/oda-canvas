import { createTheme, Theme, alpha } from '@mui/material/styles';
import { PaletteMode } from '@mui/material';

// Minimal color palette
const colors = {
  primary: {
    main: '#0F172A',
    light: '#334155',
    dark: '#020617',
  },
  accent: {
    main: '#3B82F6',
    light: '#60A5FA',
    dark: '#2563EB',
  },
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#06B6D4',
};

const getDesignTokens = (mode: PaletteMode) => ({
  palette: {
    mode,
    ...(mode === 'light'
      ? {
          primary: {
            main: colors.accent.main,
            light: colors.accent.light,
            dark: colors.accent.dark,
            contrastText: '#FFFFFF',
          },
          secondary: {
            main: colors.primary.main,
            light: colors.primary.light,
            dark: colors.primary.dark,
            contrastText: '#FFFFFF',
          },
          success: { main: colors.success },
          warning: { main: colors.warning },
          error: { main: colors.error },
          info: { main: colors.info },
          background: {
            default: '#FAFAFA',
            paper: '#FFFFFF',
          },
          text: {
            primary: '#0F172A',
            secondary: '#64748B',
          },
          divider: '#E2E8F0',
        }
      : {
          primary: {
            main: colors.accent.light,
            light: '#93C5FD',
            dark: colors.accent.main,
            contrastText: '#0F172A',
          },
          secondary: {
            main: '#E2E8F0',
            light: '#F1F5F9',
            dark: '#CBD5E1',
            contrastText: '#0F172A',
          },
          success: { main: '#34D399' },
          warning: { main: '#FBBF24' },
          error: { main: '#F87171' },
          info: { main: '#22D3EE' },
          background: {
            default: '#0F172A',
            paper: '#1E293B',
          },
          text: {
            primary: '#F1F5F9',
            secondary: '#94A3B8',
          },
          divider: '#334155',
        }),
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h1: {
      fontSize: '2.25rem',
      fontWeight: 600,
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontSize: '1.875rem',
      fontWeight: 600,
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '0.9375rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.5,
      fontWeight: 500,
    },
    button: {
      textTransform: 'none' as const,
      fontWeight: 500,
      fontSize: '0.875rem',
    },
    overline: {
      fontSize: '0.6875rem',
      fontWeight: 600,
      letterSpacing: '0.08em',
      textTransform: 'uppercase' as const,
    },
  },
  shape: {
    borderRadius: 12,
  },
  spacing: 8,
});

export const createMinimalTheme = (mode: PaletteMode): Theme => {
  const baseTheme = createTheme(getDesignTokens(mode));

  return createTheme(baseTheme, {
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            scrollbarWidth: 'thin',
            '&::-webkit-scrollbar': {
              width: '6px',
              height: '6px',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: mode === 'light' ? '#CBD5E1' : '#475569',
              borderRadius: '3px',
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: 'transparent',
            },
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
            color: baseTheme.palette.text.primary,
            boxShadow: 'none',
            borderBottom: `1px solid ${baseTheme.palette.divider}`,
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            backgroundColor: baseTheme.palette.background.paper,
            borderRight: `1px solid ${baseTheme.palette.divider}`,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundColor: baseTheme.palette.background.paper,
            borderRadius: 16,
            border: `1px solid ${baseTheme.palette.divider}`,
            boxShadow: 'none',
            transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
            '&:hover': {
              borderColor: mode === 'light' ? '#CBD5E1' : '#475569',
              boxShadow: mode === 'light'
                ? '0 4px 12px rgba(0, 0, 0, 0.05)'
                : '0 4px 12px rgba(0, 0, 0, 0.2)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
          rounded: {
            borderRadius: 16,
          },
          elevation1: {
            boxShadow: mode === 'light'
              ? '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1)'
              : '0 1px 3px rgba(0, 0, 0, 0.2), 0 1px 2px rgba(0, 0, 0, 0.3)',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            textTransform: 'none',
            fontWeight: 500,
            padding: '10px 20px',
            boxShadow: 'none',
            '&:hover': {
              boxShadow: 'none',
            },
          },
          contained: {
            '&:hover': {
              boxShadow: 'none',
            },
          },
          containedPrimary: {
            backgroundColor: colors.accent.main,
            '&:hover': {
              backgroundColor: colors.accent.dark,
            },
          },
          outlined: {
            borderColor: baseTheme.palette.divider,
            '&:hover': {
              borderColor: baseTheme.palette.text.secondary,
              backgroundColor: alpha(baseTheme.palette.text.primary, 0.04),
            },
          },
          text: {
            '&:hover': {
              backgroundColor: alpha(baseTheme.palette.text.primary, 0.04),
            },
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            '&:hover': {
              backgroundColor: alpha(baseTheme.palette.text.primary, 0.04),
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            fontWeight: 500,
            fontSize: '0.75rem',
          },
          filled: {
            backgroundColor: alpha(baseTheme.palette.text.primary, 0.08),
          },
          outlined: {
            borderColor: baseTheme.palette.divider,
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 10,
              '& fieldset': {
                borderColor: baseTheme.palette.divider,
              },
              '&:hover fieldset': {
                borderColor: baseTheme.palette.text.secondary,
              },
              '&.Mui-focused fieldset': {
                borderColor: baseTheme.palette.primary.main,
                borderWidth: '1.5px',
              },
            },
          },
        },
      },
      MuiSelect: {
        styleOverrides: {
          root: {
            borderRadius: 10,
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 20,
            boxShadow: mode === 'light'
              ? '0 25px 50px -12px rgba(0, 0, 0, 0.15)'
              : '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          },
        },
      },
      MuiDialogTitle: {
        styleOverrides: {
          root: {
            fontSize: '1.125rem',
            fontWeight: 600,
          },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
            fontSize: '0.875rem',
            minHeight: 44,
            padding: '12px 16px',
          },
        },
      },
      MuiTabs: {
        styleOverrides: {
          indicator: {
            height: 2,
            borderRadius: 1,
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: 12,
          },
          standardSuccess: {
            backgroundColor: alpha(colors.success, 0.1),
            color: mode === 'light' ? '#065F46' : '#6EE7B7',
          },
          standardError: {
            backgroundColor: alpha(colors.error, 0.1),
            color: mode === 'light' ? '#991B1B' : '#FCA5A5',
          },
          standardWarning: {
            backgroundColor: alpha(colors.warning, 0.1),
            color: mode === 'light' ? '#92400E' : '#FCD34D',
          },
          standardInfo: {
            backgroundColor: alpha(colors.info, 0.1),
            color: mode === 'light' ? '#0E7490' : '#67E8F9',
          },
        },
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            marginBottom: 4,
            '&.Mui-selected': {
              backgroundColor: alpha(baseTheme.palette.primary.main, 0.1),
              '&:hover': {
                backgroundColor: alpha(baseTheme.palette.primary.main, 0.15),
              },
            },
            '&:hover': {
              backgroundColor: alpha(baseTheme.palette.text.primary, 0.04),
            },
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            borderRadius: 4,
            height: 4,
            backgroundColor: alpha(baseTheme.palette.primary.main, 0.15),
          },
          bar: {
            borderRadius: 4,
          },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: mode === 'light' ? '#0F172A' : '#F1F5F9',
            color: mode === 'light' ? '#F1F5F9' : '#0F172A',
            fontSize: '0.75rem',
            fontWeight: 500,
            borderRadius: 8,
            padding: '8px 12px',
          },
        },
      },
      MuiDivider: {
        styleOverrides: {
          root: {
            borderColor: baseTheme.palette.divider,
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          root: {
            borderColor: baseTheme.palette.divider,
          },
          head: {
            fontWeight: 600,
            backgroundColor: alpha(baseTheme.palette.text.primary, 0.02),
          },
        },
      },
      MuiSkeleton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
          },
        },
      },
      MuiAccordion: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            border: `1px solid ${baseTheme.palette.divider}`,
            boxShadow: 'none',
            '&:before': {
              display: 'none',
            },
            '&.Mui-expanded': {
              margin: 0,
            },
          },
        },
      },
      MuiBadge: {
        styleOverrides: {
          badge: {
            fontWeight: 600,
            fontSize: '0.6875rem',
          },
        },
      },
    },
  });
};

export const lightTheme = createMinimalTheme('light');
export const darkTheme = createMinimalTheme('dark');

export const chartColors = {
  primary: colors.accent.main,
  success: colors.success,
  warning: colors.warning,
  error: colors.error,
  info: colors.info,
  series: [
    colors.accent.main,
    colors.success,
    colors.warning,
    colors.info,
    '#8B5CF6',
    '#EC4899',
    '#14B8A6',
  ],
};

export default createMinimalTheme;
