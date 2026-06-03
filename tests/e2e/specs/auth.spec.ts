import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('should show login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('text=登录')).toBeVisible()
    await expect(page.locator('input[type="text"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
  })

  test('should show validation errors for empty form', async ({ page }) => {
    await page.goto('/login')
    await page.click('button[type="submit"]')
    // Should show validation messages
    await expect(page.locator('text=请输入用户名').or(page.locator('text=required'))).toBeVisible()
  })

  test('should navigate to registration page', async ({ page }) => {
    await page.goto('/login')
    await page.click('text=注册')
    await expect(page).toHaveURL(/.*register.*/)
  })
})

test.describe('Navigation', () => {
  test('should navigate through main sections', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('nav')).toBeVisible()
    
    const navLinks = ['首页', '路径规划', '气象数据', '无人机管理']
    for (const link of navLinks) {
      const navItem = page.locator(`nav >> text=${link}`)
      if (await navItem.isVisible()) {
        await navItem.click()
        await page.waitForTimeout(500)
      }
    }
  })
})
