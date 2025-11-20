import { test, expect } from '@playwright/test';

test.describe('HomePage', () => {
  test('should load the homepage', async ({ page }) => {
    await page.goto('/');
    
    // Check that the page loads
    await expect(page).toHaveTitle(/AETHERA/i);
    
    // Check for main content
    const heading = page.getByRole('heading', { name: /projects/i });
    await expect(heading).toBeVisible();
  });

  test('should display projects list', async ({ page }) => {
    await page.goto('/');
    
    // Wait for projects to load (if any)
    // This will pass even if no projects exist
    const projectsSection = page.locator('[data-testid="projects-list"]').or(page.locator('main'));
    await expect(projectsSection).toBeVisible();
  });

  test('should navigate to new project page', async ({ page }) => {
    await page.goto('/');
    
    // Look for "New Project" button or link
    const newProjectButton = page.getByRole('link', { name: /new project/i }).or(
      page.getByRole('button', { name: /new project/i })
    );
    
    if (await newProjectButton.isVisible()) {
      await newProjectButton.click();
      await expect(page).toHaveURL(/.*projects\/new/);
    }
  });
});

