# Frontend Testing Guide

## Overview

This document describes how to set up and run tests for the BTC Options Trading frontend application.

## Test Framework

The project uses **Vitest** as the testing framework, which is optimized for Vite-based projects.

## Setup Instructions

### 1. Install Testing Dependencies

Run the following command to install the required testing packages:

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @vitest/ui
```

### 2. Update vite.config.ts

Add the test configuration to your `vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
  },
})
```

### 3. Create Test Setup File

Create `src/test/setup.ts`:

```typescript
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)

afterEach(() => {
  cleanup()
})
```

### 4. Update package.json

Add test scripts to your `package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage"
  }
}
```

## Running Tests

### Run Tests in Watch Mode

```bash
npm test
```

This will run tests in watch mode, re-running them when files change.

### Run Tests Once

```bash
npm run test:run
```

This runs all tests once and exits, useful for CI/CD pipelines.

### Run Tests with UI

```bash
npm run test:ui
```

This opens a browser-based UI for exploring and running tests.

### Run Tests with Coverage

```bash
npm run test:coverage
```

This generates a coverage report showing which parts of your code are tested.

## Test Structure

Tests are organized in `__tests__` directories next to the components they test:

```
src/
  components/
    strategy/
      __tests__/
        StrategyWizard.test.tsx
      StrategyWizard.tsx
      Step1_TemplateSelection.tsx
      Step2_ParameterConfig.tsx
      Step3_Confirmation.tsx
```

## Existing Tests

### StrategyWizard Tests

Location: `src/components/strategy/__tests__/StrategyWizard.test.tsx`

These tests verify the wizard step validation logic:

- **Step 1 - Template Selection**
  - Validates that a template must be selected
  - Tests template selection success

- **Step 2 - Parameter Configuration**
  - Tests basic field validation (expiry date, quantity)
  - Tests strategy-specific validation:
    - Single leg strategy
    - Straddle strategy
    - Strangle strategy (including strike order validation)
    - Iron condor strategy (including ascending order validation)
    - Butterfly strategy
  - Tests date validation (no past dates)
  - Tests numeric validation (positive values)

- **Step 3 - Confirmation**
  - Validates that confirmation step always passes

- **Step Navigation**
  - Tests that users cannot proceed without completing required fields
  - Tests that validation prevents invalid data submission

## Writing New Tests

When writing new tests, follow these guidelines:

1. **Test file naming**: Use `.test.tsx` or `.test.ts` suffix
2. **Test organization**: Group related tests using `describe` blocks
3. **Test naming**: Use descriptive names that explain what is being tested
4. **Arrange-Act-Assert**: Structure tests clearly:
   ```typescript
   it('should do something', () => {
     // Arrange: Set up test data
     const data = createTestData()
     
     // Act: Perform the action
     const result = performAction(data)
     
     // Assert: Verify the result
     expect(result).toBe(expected)
   })
   ```

## Best Practices

1. **Keep tests focused**: Each test should verify one specific behavior
2. **Use descriptive names**: Test names should clearly state what they test
3. **Avoid test interdependence**: Tests should be able to run in any order
4. **Mock external dependencies**: Use mocks for API calls, external services
5. **Test user behavior**: Focus on testing what users do, not implementation details
6. **Maintain test coverage**: Aim for high coverage of critical paths

## Troubleshooting

### Tests fail with "Cannot find module" errors

Make sure all testing dependencies are installed:
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

### Tests fail with DOM-related errors

Ensure `jsdom` is installed and configured in `vite.config.ts`:
```typescript
test: {
  environment: 'jsdom',
}
```

### TypeScript errors in test files

Make sure your `tsconfig.json` includes test files and has the correct types:
```json
{
  "compilerOptions": {
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  }
}
```

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
