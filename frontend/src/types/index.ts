/** Loan status values as returned by the Loan Service API. */
export type LoanStatus = 'PENDING' | 'ACTIVE' | 'RETURNED' | 'REJECTED';

/** User stored in localStorage after registration. */
export interface StoredUser {
  userId: string;
  name: string;
  email: string;
}

/** A loan as returned by the Loan Service API. */
export interface Loan {
  loan_id: string;
  isbn: string;
  user_id: string;
  status: LoanStatus;
  due_date: string | null;
  returned_at: string | null;
}

/** An overdue loan as returned by GET /loans/overdue. */
export type OverdueLoan = Loan;

/** Generic paginated API response envelope. */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}



