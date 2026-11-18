import { colors } from './colors'

export const applyTheme = () => {
  const root = document.documentElement
  Object.entries(colors).forEach(([key, value]) => {
    root.style.setProperty(`--color-${key}`, value)
  })
}