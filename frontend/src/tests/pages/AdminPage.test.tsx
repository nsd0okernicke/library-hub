import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AdminPage from "@/pages/AdminPage";
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";
import type { OverdueLoan } from "@/types";
// Use a far-past due date so daysOverdue() always returns a positive number,
// regardless of when the test runs. This avoids the need for fake timers.
const mockOverdueLoans: OverdueLoan[] = [
  {
    loan_id: "l-ov-1",
    isbn: "9780132350884",
    user_id: "user-123",
    status: "ACTIVE",
    due_date: "2020-01-01",
    returned_at: null,
  },
  {
    loan_id: "l-ov-2",
    isbn: "9781491950296",
    user_id: "user-456",
    status: "ACTIVE",
    due_date: "2020-06-15",
    returned_at: null,
  },
];
function renderAdminPage(): ReturnType<typeof render> {
  return render(
    <MemoryRouter>
      <AdminPage />
    </MemoryRouter>
  );
}
describe("AdminPage", () => {
  it("shows No overdue loans when there are none", async () => {
    renderAdminPage();
    expect(await screen.findByText(/no overdue loans/i)).toBeInTheDocument();
  });
  it("renders each overdue loan with user ID, ISBN and formatted due date", async () => {
    server.use(
      http.get("/api/loan/loans/overdue", () => HttpResponse.json({ items: mockOverdueLoans }))
    );
    renderAdminPage();
    expect(await screen.findByText("user-123")).toBeInTheDocument();
    expect(screen.getByText("user-456")).toBeInTheDocument();
    expect(screen.getByText("9780132350884")).toBeInTheDocument();
    expect(screen.getByText("9781491950296")).toBeInTheDocument();
    expect(screen.getByText("01 Jan 2020")).toBeInTheDocument();
    expect(screen.getByText("15 Jun 2020")).toBeInTheDocument();
  });
  it("displays a positive days-overdue number for past due dates", async () => {
    server.use(
      http.get("/api/loan/loans/overdue", () => HttpResponse.json({ items: mockOverdueLoans }))
    );
    renderAdminPage();
    await screen.findByText("user-123");
    // Both loans have far-past due dates, so days overdue must be > 0
    const cells = screen.getAllByText(/^\d+$/);
    cells.forEach((cell) => {
      expect(Number(cell.textContent)).toBeGreaterThan(0);
    });
  });
  it("highlights days overdue in red when greater than 0", async () => {
    server.use(
      http.get("/api/loan/loans/overdue", () => HttpResponse.json({ items: mockOverdueLoans }))
    );
    const { container } = renderAdminPage();
    await screen.findByText("user-123");
    const redSpans = container.querySelectorAll(".text-red-600");
    expect(redSpans.length).toBeGreaterThanOrEqual(2);
  });
  it("shows an error message when the API request fails", async () => {
    server.use(
      http.get("/api/loan/loans/overdue", () =>
        HttpResponse.json({ error: "Internal Server Error" }, { status: 500 })
      )
    );
    renderAdminPage();
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
  it("shows a loading state initially", () => {
    server.use(
      http.get("/api/loan/loans/overdue", () => HttpResponse.json({ items: mockOverdueLoans }))
    );
    renderAdminPage();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});