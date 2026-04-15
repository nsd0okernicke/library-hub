import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// MSW server instance – shared across all tests via setup.ts
export const server = setupServer(...handlers);

