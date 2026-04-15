import { test, expect } from '@playwright/test'
import { toggleDarkMode, toggleLightMode, getCurrentTheme } from './helpers/theme-helpers'

test.describe('Smoke Tests', () => {
  test('homepage loads without errors', async ({ page }) => {
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text())
    })
    page.on('pageerror', err => errors.push(err.message))
    
    await page.goto('/')
    await expect(page).toHaveTitle(/Mock Interview/)
    expect(errors.filter(e => !e.includes('favicon'))).toHaveLength(0)
  })

  test('login page loads', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('input[type="email"]')).toBeVisible()
  })

  test('theme toggle works', async ({ page }) => {
    await page.goto('/')
    
    await toggleLightMode(page)
    await expect(await getCurrentTheme(page)).toBe('light')
    
    await toggleDarkMode(page)
    await expect(await getCurrentTheme(page)).toBe('dark')
  })
})
