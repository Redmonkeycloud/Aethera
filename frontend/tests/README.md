# AETHERA Frontend E2E Tests

This directory contains end-to-end tests for the AETHERA frontend using Playwright.

## Test Structure

```
tests/
└── e2e/
    ├── homepage.spec.ts    # Homepage tests
    ├── map.spec.ts         # Map functionality tests
    └── projects.spec.ts    # Project management tests
```

## Running Tests

### All Tests
```bash
npm run test:e2e
```

### With UI Mode
```bash
npm run test:e2e:ui
```

### Debug Mode
```bash
npm run test:e2e:debug
```

### Specific Browser
```bash
npx playwright test --project=chromium
```

## Test Configuration

Tests are configured in `playwright.config.ts`:

- **Browsers**: Chromium, Firefox, WebKit
- **Base URL**: `http://localhost:3000` (or `VITE_API_URL` env var)
- **Screenshots**: On failure only
- **Traces**: On first retry
- **Retries**: 2 on CI, 0 locally

## Writing Tests

Example test structure:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('should do something', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

## CI/CD

E2E tests run in GitHub Actions:
- Backend API started automatically
- Tests run against all browsers
- Screenshots and traces captured on failure

