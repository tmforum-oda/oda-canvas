import { theme as antdThemeSystem } from 'antd'
import type { ThemeConfig } from 'antd'

export type ThemeMode = 'light'

export interface ColorPalette {
  bgBase: string
  bgSidebar: string
  bgCard: string
  bgTableHover: string
  surfaceSubtle: string
  surfaceMuted: string
  surfaceInset: string
  surfaceInsetStrong: string
  surfaceSelected: string
  surfaceSelectedBorder: string
  progressTrack: string
  codeBg: string
  codeHeaderBg: string
  codeText: string
  codeTextMuted: string
  primary: string
  primaryHover: string
  primaryGradient: string
  primarySurface: string
  primaryBorder: string
  hoverSurface: string
  inputBg: string
  textPrimary: string
  textSecondary: string
  textMuted: string
  border: string
  borderLight: string
  statusLive: string
  statusLiveBg: string
  statusDeprecated: string
  statusDeprecatedBg: string
  statusDown: string
  statusDownBg: string
  infoSurface: string
  infoText: string
  infoBorder: string
  tmfBg: string
  tmfText: string
  shadow: string
}

const lightPalette: ColorPalette = {
  bgBase: '#F5F7FB',
  bgSidebar: '#171A22',
  bgCard: '#FFFFFF',
  bgTableHover: '#F3F7FB',
  surfaceSubtle: '#F8FAFC',
  surfaceMuted: '#F1F5F9',
  surfaceInset: '#F8FAFC',
  surfaceInsetStrong: '#EEF4F8',
  surfaceSelected: '#EAF4FC',
  surfaceSelectedBorder: '#B7D7EB',
  progressTrack: '#E2E8F0',
  codeBg: '#10141C',
  codeHeaderBg: '#171D29',
  codeText: '#DCE6F2',
  codeTextMuted: '#94A3B8',
  primary: '#0072CE',
  primaryHover: '#005EA8',
  primaryGradient: 'linear-gradient(135deg, #E4002B 0%, #0072CE 58%, #00A88E 100%)',
  primarySurface: '#EAF4FC',
  primaryBorder: '#B7D7EB',
  hoverSurface: '#EDF3F8',
  inputBg: '#FFFFFF',
  textPrimary: '#182032',
  textSecondary: '#53627A',
  textMuted: '#78859A',
  border: '#D9E2EF',
  borderLight: '#E7EDF5',
  statusLive: '#0E8A55',
  statusLiveBg: '#EAFBF2',
  statusDeprecated: '#B56A00',
  statusDeprecatedBg: '#FFF6E6',
  statusDown: '#C92A35',
  statusDownBg: '#FFF0F1',
  infoSurface: '#EEF2FF',
  infoText: '#4752C4',
  infoBorder: '#C8D2FF',
  tmfBg: '#FDECEF',
  tmfText: '#B20022',
  shadow: '0 20px 48px rgba(16, 24, 40, 0.12)',
}

export function getThemeColors(_mode: ThemeMode = 'light'): ColorPalette {
  return lightPalette
}

export function setActiveThemeMode(_mode: ThemeMode): void {
  // single theme — no-op
}

export const colors: ColorPalette = lightPalette

export function getAntdTheme(_mode: ThemeMode = 'light'): ThemeConfig {
  const palette = lightPalette

  return {
    algorithm: antdThemeSystem.defaultAlgorithm,
    token: {
      colorPrimary: palette.primary,
      colorBgBase: palette.bgBase,
      colorBgContainer: palette.bgCard,
      colorBgElevated: palette.bgCard,
      colorBgLayout: palette.bgBase,
      colorText: palette.textPrimary,
      colorTextSecondary: palette.textSecondary,
      colorTextTertiary: palette.textMuted,
      colorBorder: palette.border,
      colorBorderSecondary: palette.borderLight,
      colorSplit: palette.border,
      borderRadius: 8,
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      fontSize: 14,
      colorLink: palette.primary,
      colorLinkHover: palette.primaryHover,
      wireframe: false,
    },
    components: {
      Layout: {
        bodyBg: palette.bgBase,
        siderBg: palette.bgSidebar,
        headerBg: palette.bgCard,
      },
      Table: {
        colorBgContainer: palette.bgCard,
        headerBg: '#F8FAFC',
        headerColor: palette.textSecondary,
        rowHoverBg: palette.bgTableHover,
        borderColor: palette.border,
        colorText: palette.textPrimary,
      },
      Card: {
        colorBgContainer: palette.bgCard,
        colorBorderSecondary: palette.border,
      },
      Button: {
        colorPrimary: palette.primary,
        colorPrimaryHover: palette.primaryHover,
        colorPrimaryActive: palette.primaryHover,
        defaultBg: palette.bgCard,
        defaultColor: palette.textSecondary,
        defaultBorderColor: palette.border,
      },
      Input: {
        colorBgContainer: palette.inputBg,
        colorBorder: palette.border,
        colorText: palette.textPrimary,
        colorTextPlaceholder: palette.textMuted,
        activeBorderColor: palette.primary,
        hoverBorderColor: palette.primary,
      },
      Select: {
        colorBgContainer: palette.inputBg,
        colorBorder: palette.border,
        colorText: palette.textPrimary,
        colorTextPlaceholder: palette.textMuted,
        optionSelectedBg: palette.primarySurface,
      },
      Modal: {
        contentBg: palette.bgCard,
        headerBg: palette.bgCard,
        titleColor: palette.textPrimary,
      },
      Tabs: {
        cardBg: palette.bgCard,
        inkBarColor: palette.primary,
        itemActiveColor: palette.primary,
        itemSelectedColor: palette.primary,
        itemColor: palette.textSecondary,
        itemHoverColor: palette.textPrimary,
        cardGutter: 4,
      },
      Tag: {
        defaultBg: palette.tmfBg,
        defaultColor: palette.tmfText,
      },
      Dropdown: {
        colorBgElevated: palette.bgCard,
        colorText: palette.textPrimary,
      },
      Tooltip: {
        colorBgSpotlight: '#101828',
        colorTextLightSolid: '#FFFFFF',
      },
      Form: {
        labelColor: palette.textSecondary,
        colorText: palette.textPrimary,
      },
      Statistic: {
        colorText: palette.textPrimary,
        titleFontSize: 13,
      },
      Badge: {
        colorBgContainer: palette.bgCard,
      },
      Spin: {
        colorPrimary: palette.primary,
      },
      Segmented: {
        trackBg: palette.bgBase,
        itemColor: palette.textSecondary,
        itemHoverColor: palette.textPrimary,
        itemSelectedColor: palette.textPrimary,
        itemSelectedBg: palette.bgCard,
      },
    },
  }
}
