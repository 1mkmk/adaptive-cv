# Frontend Tests for AdaptiveCV

This directory contains tests to verify the integration between the frontend and backend components of the AdaptiveCV application.

## Test Structure

The main test file is `backend-integration.test.ts`, which provides basic verification of:

1. API base URL configuration
2. Profile service functionality 
3. Job management functionality
4. CV generation service

## Running Tests

To run the tests:

```bash
# Run integration tests
npm test

# Run all tests (may include services unit tests)
npm run test:all

# Run tests in watch mode
npm run test:watch
```

## Test Coverage

The tests verify the following aspects:

1. API URL configuration is correct
2. Profile data can be loaded and saved
3. Job listings can be retrieved and new jobs can be created
4. CV generation produces expected output

## Additional Testing

For thorough testing, consider adding:

1. More detailed unit tests for each service
2. Integration tests that use mock API responses
3. UI component tests
4. End-to-end tests with real API calls (using a test database)

The current tests are designed to be simple and reliable for basic verification of the frontend-backend integration, especially when setting up a new development environment.

## Adding New Tests

When adding new functionality, please add corresponding tests in this directory to ensure the backend integration continues to function correctly.