import React, { createContext, useContext, useEffect } from 'react'
import type { ReactNode } from 'react'
import type { ThemeConfig } from 'antd'
import { getAntdTheme, getThemeColors, type ThemeMode } from './palette'

interface ThemeModeContextValue {
  mode: ThemeMode
  setMode: (mode: ThemeMode) => void
  toggleMode: () => void
  antdTheme: ThemeConfig
}

const ThemeModeContext = createContext<ThemeModeContextValue | null>(null)

const FIXED_MODE: ThemeMode = 'light'

export function ThemeModeProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const palette = getThemeColors(FIXED_MODE)
    document.documentElement.dataset.theme = FIXED_MODE
    document.documentElement.style.colorScheme = FIXED_MODE
    document.body.style.background = palette.bgBase
    document.body.style.color = palette.textPrimary
  }, [])

  const value: ThemeModeContextValue = {
    mode: FIXED_MODE,
    setMode: () => {},
    toggleMode: () => {},
    antdTheme: getAntdTheme(FIXED_MODE),
  }

  return <ThemeModeContext.Provider value={value}>{children}</ThemeModeContext.Provider>
}

export function useThemeMode(): ThemeModeContextValue {
  const context = useContext(ThemeModeContext)

  if (!context) {
    throw new Error('useThemeMode must be used inside ThemeModeProvider')
  }

  return context
}
