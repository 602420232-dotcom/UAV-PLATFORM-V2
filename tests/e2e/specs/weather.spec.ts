import { test, expect } from '@playwright/test'

test.describe('Weather Page', () => {
  test('should display weather data components', async ({ page }) => {
    await page.goto('/weather')
    await expect(page.locator('text=气象数据').or(page.locator('text=Weather Data'))).toBeVisible()
  })

  test('should have working data filters', async ({ page }) => {
    await page.goto('/weather')
    // Check for filter controls
    const filterSelects = page.locator('select, .ant-select')
    const filterCount = await filterSelects.count()
    expect(filterCount).toBeGreaterThanOrEqual(1)
  })
})

test.describe('Path Planning', () => {
  test('should display planning interface', async ({ page }) => {
    await page.goto('/planning')
    await expect(page.locator('text=路径规划').or(page.locator('text=Path Planning'))).toBeVisible()
  })

  test('should have map component', async ({ page }) => {
    await page.goto('/planning')
    await page.waitForTimeout(2000)
    // Check for map canvas
    const canvas = page.locator('canvas')
    const canvasCount = await canvas.count()
    expect(canvasCount).toBeGreaterThanOrEqual(1)
  })
})
