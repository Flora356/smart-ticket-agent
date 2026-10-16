import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Bot,
  Check,
  ChevronRight,
  CircleDot,
  Clock3,
  Database,
  Gauge,
  Loader2,
  MessageSquareText,
  RefreshCw,
  Send,
  ShieldAlert,
  Sparkles,
  TicketCheck,
  UserRound,
  X,
} from "lucide-react";
import {
  createTicket,
  decideTicket,
  getBenchmark,
  getHealth,
  getTicket,
  listTickets,
} from "./api";
import type {
  AgentTrace,
  BenchmarkReport,
  Health,
  TicketDetail,
  TicketSummary,
} from "./types";

const categoryLabel: Record<string, string> = {
  network_pairing: "配网问题",
  device_fault: "设备故障",
  order_after_sales: "订单售后",
  refund: "退款",
  account_security: "账号安全",
  complaint: "投诉建议",
  other: "其他",
};

const statusLabel: Record<string, string> = {
  CREATED: "已创建",
  PARSING: "理解中",
  PARSED: "已理解",
  PROCESSING: "处理中",
  DRAFTED: "已起草",
  REVIEWING: "质检中",
  APPROVED: "已通过",
  REPLIED: "已回复",
  CLOSED: "已关闭",
  NEED_HUMAN: "待人工",
  FAILED: "失败",
  RETRYING: "重试中",
  REJECTED: "已拒绝",
};

const actionLabel: Record<string, string> = {
  auto_reply: "自动回复",
  human_review: "转人工",
  retry: "重试",
  reject: "拒绝",
  auto_close: "自动关闭",
};

const stepLabel: Record<string, string> = {
  understand_agent: "理解 Agent",
  process_agent: "处理 Agent",
  respond_agent: "回复 Agent",
  qc_agent: "质检 Agent",
  workflow: "工作流",
};

function riskClass(level?: string | null) {
  if (level === "critical") return "risk risk-critical";
  if (level === "high") return "risk risk-high";
  if (level === "medium") return "risk risk-medium";
  return "risk risk-low";
}

function statusClass(status: string) {
  if (status === "CLOSED") return "status status-closed";
  if (status === "NEED_HUMAN") return "status status-human";
  if (status === "FAILED" || status === "REJECTED") return "status status-danger";
  return "status status-active";
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>
  );
}

function TraceCard({ trace }: { trace: AgentTrace }) {
  const [open, setOpen] = useState(false);
  return (
    <button className="trace-card" onClick={() => setOpen((value) => !value)}>
      <span className="trace-icon">
        <Bot size={15} />
      </span>
      <span className="trace-main">
        <span className="trace-title">
          {stepLabel[trace.step_name] ?? trace.step_name}
          {trace.status === "success" ? (
            <Check size={14} className="ok-icon" />
          ) : (
            <X size={14} className="bad-icon" />
          )}
        </span>
        <span className="trace-meta">
          {trace.latency_ms}ms
          <ChevronRight size={13} className={open ? "chevron open" : "chevron"} />
        </span>
      </span>
      {open && (
        <span className="trace-detail">
          <span className="detail-label">输入</span>
          <JsonBlock value={trace.input} />
          <span className="detail-label">输出</span>
          <JsonBlock value={trace.output} />
        </span>
      )}
    </button>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-mark">
        <Sparkles size={26} />
      </div>
      <h2>选择一条工单开始查看</h2>
      <p>左侧提交新工单，或从队列中选择一条，查看 Agent 处理链路与评测结果。</p>
    </div>
  );
}

export default function App() {
  const [tickets, setTickets] = useState<TicketSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkReport | null>(null);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [activePane, setActivePane] = useState<"trace" | "events">("trace");

  async function refresh() {
    setRefreshing(true);
    try {
      const [ticketResponse, healthResponse, benchmarkResponse] = await Promise.all([
        listTickets(),
        getHealth(),
        getBenchmark(),
      ]);
      setTickets(ticketResponse.items);
      setHealth(healthResponse);
      setBenchmark(benchmarkResponse);
      if (selectedId) {
        setDetail(await getTicket(selectedId));
      }
      setError("");
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "连接后端失败",
      );
    } finally {
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function selectTicket(id: number) {
    setSelectedId(id);
    try {
      setDetail(await getTicket(id));
      setError("");
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "加载工单失败",
      );
    }
  }

  async function submitTicket() {
    if (!draft.trim() || loading) return;
    setLoading(true);
    setError("");
    try {
      const created = await createTicket(draft.trim());
      setDraft("");
      setSelectedId(created.ticket.id);
      setDetail(created);
      const response = await listTickets();
      setTickets(response.items);
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "提交工单失败",
      );
    } finally {
      setLoading(false);
    }
  }

  async function submitDecision(decision: "approve" | "close" | "reject") {
    if (!selectedId) return;
    try {
      setDetail(await decideTicket(selectedId, decision));
      await refresh();
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "提交决策失败",
      );
    }
  }

  const healthCounts = useMemo(
    () =>
      Object.entries(health?.status_counts ?? {}).map(([key, value]) => ({
        key,
        value,
      })),
    [health],
  );

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <TicketCheck size={19} />
          </div>
          <div>
            <div className="brand-title">智能工单 Agent</div>
            <div className="brand-subtitle">Quality Workbench</div>
          </div>
        </div>

        <div className="top-status">
          <span className="live-dot" />
          <span>{health?.status === "ok" ? "后端在线" : "正在连接"}</span>
          <span className="divider" />
          <Database size={14} />
          <span>{health?.model ?? "—"}</span>
          <button
            className="icon-button"
            onClick={() => void refresh()}
            title="刷新数据"
          >
            <RefreshCw size={15} className={refreshing ? "spin" : ""} />
          </button>
        </div>
      </header>

      <main className="workspace">
        <aside className="queue-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">INBOX</span>
              <h1>工单队列</h1>
            </div>
            <span className="count-badge">{tickets.length}</span>
          </div>

          <div className="composer">
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                  void submitTicket();
                }
              }}
              placeholder="描述一个用户问题，例如：AF205 配网失败，提示 E104"
              rows={3}
            />
            <div className="composer-footer">
              <span>Ctrl + Enter 提交</span>
              <button
                className="primary-button"
                onClick={() => void submitTicket()}
                disabled={!draft.trim() || loading}
              >
                {loading ? (
                  <Loader2 size={15} className="spin" />
                ) : (
                  <Send size={15} />
                )}
                运行 Agent
              </button>
            </div>
          </div>

          <div className="queue-list">
            {tickets.length === 0 && (
              <div className="queue-empty">还没有工单，提交一条试试。</div>
            )}
            {tickets.map((ticket) => (
              <button
                key={ticket.id}
                className={
                  selectedId === ticket.id
                    ? "queue-item queue-item-active"
                    : "queue-item"
                }
                onClick={() => void selectTicket(ticket.id)}
              >
                <span className="queue-topline">
                  <span className="ticket-number">#{ticket.id}</span>
                  <span className={statusClass(ticket.status)}>
                    {statusLabel[ticket.status] ?? ticket.status}
                  </span>
                </span>
                <span className="queue-title">{ticket.raw_content}</span>
                <span className="queue-bottomline">
                  <span>{categoryLabel[ticket.category ?? ""] ?? "未分类"}</span>
                  <span>{ticket.priority ?? "—"}</span>
                  <span>{ticket.assigned_group ?? "未路由"}</span>
                  <span>{formatTime(ticket.updated_at)}</span>
                </span>
              </button>
            ))}
          </div>
        </aside>

        <section className="conversation-panel">
          <div className="panel-heading compact">
            <div>
              <span className="eyebrow">CONVERSATION</span>
              <h2>工单处理</h2>
            </div>
            {detail && (
              <span className={statusClass(detail.ticket.status)}>
                {statusLabel[detail.ticket.status] ?? detail.ticket.status}
              </span>
            )}
          </div>

          {!detail ? (
            <EmptyState />
          ) : (
            <>
              <div className="chat-scroll">
                <div className="message-row user-message">
                  <div className="message-avatar user-avatar">
                    <UserRound size={15} />
                  </div>
                  <div className="message-bubble">
                    <div className="message-meta">
                      <span>用户</span>
                      <span>{formatTime(detail.ticket.created_at)}</span>
                    </div>
                    <p>{detail.content.raw}</p>
                  </div>
                </div>

                <div className="message-row agent-message">
                  <div className="message-avatar agent-avatar">
                    <Bot size={15} />
                  </div>
                  <div className="message-bubble agent-bubble">
                    <div className="message-meta">
                      <span>Agent 处理结果</span>
                      <span>{actionLabel[detail.ticket.final_action ?? ""] ?? "—"}</span>
                    </div>
                    <p>{detail.content.reply_draft ?? "尚未生成回复"}</p>
                    <div className="insight-strip">
                      <span>
                        <CircleDot size={13} />
                        {categoryLabel[detail.ticket.category ?? ""] ?? "未分类"}
                      </span>
                      <span>
                        <Gauge size={13} />
                        {detail.ticket.priority ?? "—"}
                      </span>
                      <span>
                        <Activity size={13} />
                        {detail.ticket.assigned_group ?? "未路由"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="decision-bar">
                {detail.ticket.status === "NEED_HUMAN" ? (
                  <>
                    <span className="decision-hint">
                      <ShieldAlert size={14} />
                      此工单需要人工确认
                    </span>
                    <button
                      className="secondary-button"
                      onClick={() => void submitDecision("reject")}
                    >
                      <X size={14} />
                      拒绝
                    </button>
                    <button
                      className="secondary-button"
                      onClick={() => void submitDecision("close")}
                    >
                      <TicketCheck size={14} />
                      直接关闭
                    </button>
                    <button
                      className="primary-button"
                      onClick={() => void submitDecision("approve")}
                    >
                      <Check size={14} />
                      确认处理
                    </button>
                  </>
                ) : (
                  <span className="decision-hint">
                    <Clock3 size={14} />
                    当前工单已由 Agent 完成处理
                  </span>
                )}
              </div>
            </>
          )}
        </section>

        <aside className="inspector-panel">
          <div className="panel-heading compact">
            <div>
              <span className="eyebrow">INSPECTOR</span>
              <h2>质量与链路</h2>
            </div>
          </div>

          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Agent 步骤</span>
              <strong>{detail?.traces.length ?? 0}</strong>
              <span className="stat-foot">Trace 记录</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">风险</span>
              <strong className={riskClass(detail?.ticket.risk_level).replace("risk ", "")}>
                {detail?.ticket.risk_level?.toUpperCase() ?? "—"}
              </strong>
              <span className="stat-foot">自动判定</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">评测</span>
              <strong>
                {benchmark?.available
                  ? `${Math.round((benchmark.case_pass_rate ?? 0) * 100)}%`
                  : "—"}
              </strong>
              <span className="stat-foot">
                {benchmark?.passed_cases ?? 0}/{benchmark?.total_cases ?? 0} 用例
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">健康状态</span>
              <strong>{health?.status === "ok" ? "OK" : "—"}</strong>
              <span className="stat-foot">{health?.provider ?? "—"}</span>
            </div>
          </div>

          <div className="tabs">
            <button
              className={activePane === "trace" ? "tab tab-active" : "tab"}
              onClick={() => setActivePane("trace")}
            >
              Agent Trace
            </button>
            <button
              className={activePane === "events" ? "tab tab-active" : "tab"}
              onClick={() => setActivePane("events")}
            >
              状态事件
            </button>
          </div>

          <div className="inspector-scroll">
            {!detail && (
              <div className="inspector-empty">
                <Activity size={22} />
                <span>选择工单后查看处理链路</span>
              </div>
            )}
            {detail && activePane === "trace" && (
              <div className="trace-list">
                {detail.traces.map((trace) => (
                  <TraceCard key={trace.id} trace={trace} />
                ))}
              </div>
            )}
            {detail && activePane === "events" && (
              <div className="event-list">
                {detail.events.map((event) => (
                  <div className="event-item" key={event.id}>
                    <span className="event-dot" />
                    <div>
                      <strong>
                        {event.from_status
                          ? `${event.from_status} → ${event.to_status}`
                          : event.to_status}
                      </strong>
                      <span>{event.event_type}</span>
                      <small>{formatTime(event.created_at)}</small>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="benchmark-card">
              <div className="benchmark-head">
                <span>
                  <MessageSquareText size={14} />
                  Benchmark
                </span>
                <span>{benchmark?.available ? "已就绪" : "未运行"}</span>
              </div>
              {benchmark?.available ? (
                <>
                  <div className="progress-bar">
                    <span
                      style={{
                        width: `${(benchmark.assertion_pass_rate ?? 0) * 100}%`,
                      }}
                    />
                  </div>
                  <div className="benchmark-footer">
                    <span>
                      断言 {(benchmark.passed_assertions ?? 0)}/
                      {benchmark.total_assertions ?? 0}
                    </span>
                    <span>
                      {Math.round((benchmark.assertion_pass_rate ?? 0) * 100)}%
                    </span>
                  </div>
                </>
              ) : (
                <p className="benchmark-empty">
                  运行 Benchmark 后，这里会显示质量基线。
                </p>
              )}
            </div>

            <div className="health-card">
              <div className="benchmark-head">
                <span>
                  <AlertTriangle size={14} />
                  运行状态
                </span>
              </div>
              {healthCounts.length > 0 ? (
                <div className="health-list">
                  {healthCounts.map((item) => (
                    <div key={item.key}>
                      <span>{statusLabel[item.key] ?? item.key}</span>
                      <strong>{item.value}</strong>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="benchmark-empty">暂无工单统计。</p>
              )}
            </div>
          </div>
        </aside>
      </main>

      {error && (
        <div className="toast toast-error">
          <AlertTriangle size={15} />
          {error}
        </div>
      )}
    </div>
  );
}
