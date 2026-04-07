import { useState, useEffect } from 'react'

export function useTheme() {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const saved = localStorage.getItem('imaginaree-theme')
    return (saved === 'light') ? 'light' : 'dark'
  })

  useEffect(() => {
    localStorage.setItem('imaginaree-theme', theme)
    document.documentElement.classList.toggle('light', theme === 'light')
  }, [theme])

  const toggle = () => setTheme(theme === 'dark' ? 'light' : 'dark')

  return { theme, toggle }
}
