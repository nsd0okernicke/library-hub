import '@testing-library/jest-dom';
import { afterEach, beforeAll, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './mocks/server';

// Start MSW server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));

// Reset handlers after each test to avoid test pollution
afterEach(() => {
  cleanup();
  server.resetHandlers();
});

// Stop server after all tests
afterAll(() => server.close());

