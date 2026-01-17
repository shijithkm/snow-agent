export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export async function getAlerts() {
  const res = await fetch(`${API_BASE}/alerts`);
  return res.json();
}

export async function getTickets() {
  const res = await fetch(`${API_BASE}/tickets`);
  return res.json();
}

export async function processTicket(description: string, alert_id?: string) {
  const res = await fetch(`${API_BASE}/process_ticket`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description, alert_id })
  });
  return res.json();
}