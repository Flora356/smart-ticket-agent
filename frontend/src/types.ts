export type TicketSummary = {
  id: number;
  user_id: string;
  raw_content: string;
  category: string | null;
  priority: string | null;
  status: string;
  assigned_group: string | null;
  final_action: string | null;
  risk_level: string | null;
  created_at: string;
  updated_at: string;
};

export type TicketEvent = {
  id: number;
  from_status: string | null;
  to_status: string;
  event_type: string;
  operator: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type AgentTrace = {
  id: number;
  step_name: string;
  status: string;
  latency_ms: number;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  created_at: string;
};

export type TicketDetail = {
  ticket: TicketSummary;
  content: {
    raw: string;
    normalized: string | null;
    reply_draft: string | null;
  };
  events: TicketEvent[];
  traces: AgentTrace[];
  cost_units: number;
  analysis: {
    understood?: Record<string, unknown>;
    processed?: Record<string, unknown>;
    responded?: Record<string, unknown>;
    qc?: Record<string, unknown>;
  };
};

export type Health = {
  status: string;
  provider: string;
  model: string;
  database: string;
  status_counts: Record<string, number>;
};

export type BenchmarkReport = {
  available: boolean;
  message?: string;
  total_cases?: number;
  passed_cases?: number;
  total_assertions?: number;
  passed_assertions?: number;
  case_pass_rate?: number;
  assertion_pass_rate?: number;
  failures?: string[];
};
