import type {
  BenchmarkReport,
  Health,
  TicketDetail,
  TicketSummary,
} from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getHealth() {
  return request<Health>("/api/health");
}

export function listTickets() {
  return request<{ items: TicketSummary[] }>("/api/tickets");
}

export function getTicket(id: number) {
  return request<TicketDetail>(`/api/tickets/${id}`);
}

export function createTicket(text: string) {
  return request<TicketDetail>("/api/tickets", {
    method: "POST",
    body: JSON.stringify({ text, user_id: "web-user" }),
  });
}

export function decideTicket(
  id: number,
  decision: "approve" | "close" | "reject",
) {
  return request<TicketDetail>(`/api/tickets/${id}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision, operator: "human-agent" }),
  });
}

export function getBenchmark() {
  return request<BenchmarkReport>("/api/benchmark");
}
