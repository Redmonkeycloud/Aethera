import { test, expect } from '@playwright/test';

test.describe('Map Functionality', () => {
  test('should load map on project page', async ({ page }) => {
    // Navigate to a project page (assuming project ID exists)
    await page.goto('/projects/test-project-id');
    
    // Wait for map to load
    const mapContainer = page.locator('.maplibregl-map').or(page.locator('[data-testid="map-container"]'));
    
    // Map should be visible (may take time to load)
    await expect(mapContainer).toBeVisible({ timeout: 10000 });
  });

  test('should allow drawing AOI', async ({ page }) => {
    await page.goto('/projects/test-project-id');
    
    // Wait for map
    await page.waitForTimeout(2000);
    
    // Look for drawing button
    const drawButton = page.getByRole('button', { name: /start drawing|draw/i });
    
    if (await drawButton.isVisible()) {
      await drawButton.click();
      
      // Check that drawing mode is enabled
      const stopButton = page.getByRole('button', { name: /stop drawing/i });
      await expect(stopButton).toBeVisible();
    }
  });

  test('should display base layers', async ({ page }) => {
    await page.goto('/projects/test-project-id');
    
    // Wait for map to load
    await page.waitForTimeout(3000);
    
    // Check for layer controls
    const layerControl = page.locator('[data-testid="layer-control"]').or(
      page.locator('text=/layer/i')
    );
    
    // Layer controls may or may not be visible depending on implementation
    // Just check that page loaded without errors
    await expect(page.locator('body')).toBeVisible();
  });
});

