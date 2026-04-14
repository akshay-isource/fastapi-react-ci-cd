import React, { useState, useRef, useCallback } from "react";

const RESEARCH_API_URL = process.env.REACT_APP_RESEARCH_API_URL || "http://localhost:8001";

const AGENT_NAMES = {
  dispatcher: "Dispatcher",
  news_researcher: "News Researcher",
  academic_researcher: "Academic Researcher",
  stats_researcher: "Stats Researcher",
  research_merger: "Research Merger",
  analyst: "Analyst",
  quality_checker: "Quality Checker",
  writer: "Writer",
};

const PIPELINE_AGENTS = [
  { id: "dispatcher", label: "Dispatch", group: "dispatch" },
  { id: "news_researcher", label: "News", group: "researchers" },
  { id: "academic_researcher", label: "Academic", group: "researchers" },
  { id: "stats_researcher", label: "Stats", group: "researchers" },
  { id: "research_merger", label: "Merger", group: "process" },
  { id: "analyst", label: "Analyst", group: "process" },
  { id: "quality_checker", label: "Quality", group: "process" },
  { id: "writer", label: "Writer", group: "output" },
];

function ResearchPage() {
  const [query, setQuery] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [agentStates, setAgentStates] = useState({});
  const [logs, setLogs] = useState([]);
  const [report, setReport] = useState("");
  const [researchData, setResearchData] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [qualityScore, setQualityScore] = useState(null);
  const [qualityFeedback, setQualityFeedback] = useState("");
  const [retryCount, setRetryCount] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [expandedPanels, setExpandedPanels] = useState({});
  const timerRef = useRef(null);
  const logEndRef = useRef(null);

  const addLog = useCallback((message, type = "") => {
    const time = new Date().toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    setLogs((prev) => [...prev, { time, message, type }]);
  }, []);

  const resetState = () => {
    setAgentStates({});
    setLogs([]);
    setReport("");
    setResearchData("");
    setAnalysis("");
    setQualityScore(null);
    setQualityFeedback("");
    setRetryCount(0);
    setElapsed(0);
  };

  const setAgentStatus = (agent, status) => {
    setAgentStates((prev) => ({ ...prev, [agent]: status }));
  };

  const handleEvent = useCallback(
    (event) => {
      const { agent, status, data } = event;

      if (agent === "pipeline" && status === "done") {
        addLog("Pipeline completed successfully", "success");
        return;
      }

      // Handle dispatcher on retry
      if (agent === "dispatcher" && retryCount > 0) {
        addLog(`Retry #${retryCount} — re-routing researchers with targeted feedback`, "retry");
        setAgentStatus("news_researcher", "running");
        setAgentStatus("academic_researcher", "running");
        setAgentStatus("stats_researcher", "running");
        setAgentStatus("research_merger", "");
        setAgentStatus("analyst", "");
        setAgentStatus("quality_checker", "");
        setAgentStatus("writer", "");
        return;
      }

      // Mark agent completed
      setAgentStatus(agent, "completed");
      addLog(`${AGENT_NAMES[agent] || agent} completed`, "");

      // Set next agents as running
      if (agent === "dispatcher") {
        setAgentStatus("news_researcher", "running");
        setAgentStatus("academic_researcher", "running");
        setAgentStatus("stats_researcher", "running");
      }
      if (["news_researcher", "academic_researcher", "stats_researcher"].includes(agent)) {
        // Check if all researchers done
        setAgentStates((prev) => {
          const updated = { ...prev, [agent]: "completed" };
          const allDone = ["news_researcher", "academic_researcher", "stats_researcher"].every(
            (a) => updated[a] === "completed"
          );
          if (allDone) return { ...updated, research_merger: "running" };
          return updated;
        });
      }
      if (agent === "research_merger") setAgentStatus("analyst", "running");
      if (agent === "analyst") setAgentStatus("quality_checker", "running");
      if (agent === "quality_checker" && data?.quality_score >= 7) {
        setAgentStatus("writer", "running");
      }

      // Handle agent data
      if (agent === "quality_checker" && data) {
        const score = data.quality_score || 0;
        setQualityScore(score);
        setQualityFeedback(data.feedback || "");
        if (score < 7) {
          setRetryCount((prev) => prev + 1);
          addLog(`Quality score: ${score}/10 — triggering retry`, "retry");
          setAgentStatus("quality_checker", "retry");
          setTimeout(() => setAgentStatus("quality_checker", "completed"), 1500);
        } else {
          addLog(`Quality score: ${score}/10 — proceeding to Writer`, "success");
        }
      }

      if (agent === "research_merger" && data?.research_data) {
        setResearchData(data.research_data);
      }

      if (agent === "analyst" && data?.analysis) {
        setAnalysis(data.analysis);
      }

      if (agent === "writer" && data?.final_report) {
        setReport(data.final_report);
      }
    },
    [retryCount, addLog]
  );

  const startResearch = async () => {
    if (!query.trim() || isRunning) return;

    resetState();
    setIsRunning(true);
    addLog(`Pipeline started for: "${query}"`, "success");
    setAgentStatus("dispatcher", "running");

    // Start timer
    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      setElapsed(((Date.now() - startTime) / 1000).toFixed(1));
    }, 100);

    try {
      const response = await fetch(`${RESEARCH_API_URL}/research/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            try {
              const data = JSON.parse(trimmed.slice(6));
              handleEvent(data);
            } catch {
              // Skip malformed JSON
            }
          }
        }
      }
    } catch (err) {
      addLog(`Error: ${err.message}`, "error");
    } finally {
      clearInterval(timerRef.current);
      setIsRunning(false);
    }
  };

  const togglePanel = (id) => {
    setExpandedPanels((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const renderMarkdown = (text) => {
    if (!text) return "";
    return text
      .replace(/^### (.+)$/gm, '<h4 class="rp-md-h4">$1</h4>')
      .replace(/^## (.+)$/gm, '<h3 class="rp-md-h3">$1</h3>')
      .replace(/^# (.+)$/gm, '<h2 class="rp-md-h2">$1</h2>')
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`(.+?)`/g, '<code class="rp-md-code">$1</code>')
      .replace(/^- (.+)$/gm, '<li class="rp-md-li">$1</li>')
      .replace(/(<li.*<\/li>\n?)+/g, '<ul class="rp-md-ul">$&</ul>')
      .replace(/^(?!<[hul]|<li|<strong|<em|<code)(.+)$/gm, '<p class="rp-md-p">$1</p>')
      .replace(/\n{2,}/g, "");
  };

  const getNodeClass = (id) => {
    const state = agentStates[id] || "";
    return `rp-agent-node ${state}`;
  };

  const scoreColor =
    qualityScore >= 7
      ? "var(--accent-green)"
      : qualityScore >= 4
      ? "var(--accent-orange)"
      : "var(--accent-red)";

  return (
    <>
      {/* Search Input */}
      <div className="card">
        <div className="card-header">
          <h2>AI Research Assistant</h2>
          {isRunning && (
            <span className="badge badge-active">{elapsed}s</span>
          )}
          {!isRunning && report && (
            <span className="badge badge-active">Complete</span>
          )}
        </div>
        <div className="rp-search-bar">
          <input
            type="text"
            className="rp-search-input"
            placeholder="Enter your research topic..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && startResearch()}
            disabled={isRunning}
          />
          <button
            className="btn rp-search-btn"
            onClick={startResearch}
            disabled={isRunning || !query.trim()}
          >
            {isRunning ? "Researching..." : "Research"}
          </button>
        </div>
      </div>

      {/* Agent Pipeline */}
      <div className="card">
        <div className="card-header">
          <h2>Agent Pipeline</h2>
          {retryCount > 0 && (
            <span className="badge rp-badge-retry">
              Retry #{retryCount}
            </span>
          )}
        </div>
        <div className="rp-pipeline">
          {PIPELINE_AGENTS.map((agent, i) => (
            <React.Fragment key={agent.id}>
              <div className={getNodeClass(agent.id)} title={AGENT_NAMES[agent.id]}>
                <div className="rp-node-dot">
                  {agentStates[agent.id] === "completed" && (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                  {agentStates[agent.id] === "running" && (
                    <div className="pulse-dot"></div>
                  )}
                  {agentStates[agent.id] === "retry" && (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                    </svg>
                  )}
                </div>
                <span className="rp-node-label">{agent.label}</span>
              </div>
              {i < PIPELINE_AGENTS.length - 1 && (
                <div
                  className={`rp-pipeline-connector ${
                    agentStates[agent.id] === "completed" ? "done" : ""
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Results Grid */}
      <div className="two-col">
        {/* Report */}
        <div className="card">
          <div className="card-header">
            <h2>Research Report</h2>
          </div>
          {report ? (
            <div
              className="rp-report-content"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(report) }}
            />
          ) : (
            <div className="empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <p>Enter a topic and click Research to generate a report.</p>
              <p className="sub-text">
                The pipeline runs 3 researchers in parallel, analyzes results,
                checks quality, and writes a polished report.
              </p>
            </div>
          )}
        </div>

        {/* Side Panel */}
        <div className="rp-side-panel">
          {/* Quality Score */}
          {qualityScore !== null && (
            <div className="card rp-side-card">
              <div
                className="rp-collapsible-header"
                onClick={() => togglePanel("quality")}
              >
                <h3>Quality Assessment</h3>
                <div className="rp-score-badge" style={{ background: scoreColor + "22", color: scoreColor, borderColor: scoreColor + "44" }}>
                  {qualityScore}/10
                </div>
              </div>
              <p className="rp-detail-text">{qualityFeedback}</p>
            </div>
          )}

          {/* Research Data */}
          {researchData && (
            <div className="card rp-side-card">
              <div
                className="rp-collapsible-header"
                onClick={() => togglePanel("research")}
              >
                <h3>Research Data</h3>
                <span className="rp-chevron">{expandedPanels.research ? "\u25B2" : "\u25BC"}</span>
              </div>
              {expandedPanels.research && (
                <pre className="rp-detail-pre">{researchData}</pre>
              )}
            </div>
          )}

          {/* Analysis */}
          {analysis && (
            <div className="card rp-side-card">
              <div
                className="rp-collapsible-header"
                onClick={() => togglePanel("analysis")}
              >
                <h3>Analysis</h3>
                <span className="rp-chevron">{expandedPanels.analysis ? "\u25B2" : "\u25BC"}</span>
              </div>
              {expandedPanels.analysis && (
                <pre className="rp-detail-pre">{analysis}</pre>
              )}
            </div>
          )}

          {/* Activity Log */}
          <div className="card rp-side-card">
            <div className="card-header">
              <h2>Activity Log</h2>
            </div>
            <div className="rp-log-body">
              {logs.length === 0 ? (
                <p className="rp-log-empty">Waiting for pipeline to start...</p>
              ) : (
                logs.map((log, i) => (
                  <div className={`rp-log-entry ${log.type}`} key={i}>
                    <span className="rp-log-time">[{log.time}]</span>
                    <span className="rp-log-msg">{log.message}</span>
                  </div>
                ))
              )}
              <div ref={logEndRef} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default ResearchPage;
