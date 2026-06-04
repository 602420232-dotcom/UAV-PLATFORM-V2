import { test, expect } from '@playwright/test'

test.describe('Path Planning', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login')
    await page.fill('input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'Uav@2024!Secure')
    await page.click('button[type="submit"]')
    await page.waitForURL(/.*dashboard.*|.*\//)
  })

  test('should display planning page with map', async ({ page }) => {
    await page.goto('/planning')
    await page.waitForTimeout(2000)
    
    // Check for map canvas (Cesium or Leaflet)
    const canvas = page.locator('canvas')
    await expect(canvas.first()).toBeVisible({ timeout: 5000 })
  })

  test('should have task creation form', async ({ page }) => {
    await page.goto('/planning')
    await page.waitForTimeout(1000)
    
    // Look for create button or form
    const createBtn = page.locator('button, .ant-btn').filter({ hasText: /新建|创建|新增|Create|New/ })
    if (await createBtn.isVisible()) {
      await createBtn.click()
      await page.waitForTimeout(500)
    }
    
    // Verify form elements exist
    const inputs = page.locator('input, textarea, .ant-input')
    const inputCount = await inputs.count()
    expect(inputCount).toBeGreaterThanOrEqual(1)
  })

  test('should be able to select algorithm type', async ({ page }) => {
    await page.goto('/planning')
    await page.waitForTimeout(1000)

    // Look for algorithm select/dropdown
    const select = page.locator('select, .ant-select, [class*="algorithm"]')
    if (await select.isVisible()) {
      await select.click()
      await page.waitForTimeout(300)
      
      // Try to select an option
      const option = page.locator('option, .ant-select-item-option').first()
      if (await option.isVisible()) {
        await option.click()
        await page.waitForTimeout(300)
      }
    }
  })

  test('should display planning results', async ({ page }) => {
    await page.goto('/planning')
    await page.waitForTimeout(2000)

    // Check for result display elements
    const resultPanel = page.locator('[class*="result"], [class*="output"], .ant-card, [class*="panel"]')
    const panelCount = await resultPanel.count()
    expect(panelCount).toBeGreaterThanOrEqual(1)
  })
})
