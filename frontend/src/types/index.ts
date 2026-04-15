/** Loan status values as returned by the Loan Service API. */
export type LoanStatus = 'PENDING' | 'ACTIVE' | 'RETURNED' | 'REJECTED';

/** User stored in localStorage after registration. */
export interface StoredUser {
  userId: string;
  name: string;
  email: string;
}

/** Generic paginated API response envelope. */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

