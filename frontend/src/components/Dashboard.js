import React, { useState } from "react";
import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "/api";

const PIPELINE_STEPS = [
  { id: "prompt", label: "Prompt", status: "done", desc: "AI receives user input" },
  { id: "prd", label: "PRD", status: "done", desc: "Product requirement doc generated" },
  { id: "feature", label: "Feature", status: "done", desc: "Feature specs broken down" },
  { id: "jira", label: "JIRA", status: "active", desc: "Tickets created & assigned" },
  { id: "dev", label: "Dev", status: "pending", desc: "Development in progress" },
  { id: "qa", label: "QA", status: "pending", desc: "Quality assurance testing" },
  { id: "deploy", label: "Deploy", status: "pending", desc: "Production deployment" },
];

const STATS = [
  { label: "Active PRDs", value: "3", change: "+1 this week", color: "var(--accent-blue)" },
  { label: "Features in Dev", value: "5", change: "2 in review", color: "var(--accent-purple)" },
  { label: "JIRA Tickets", value: "12", change: "4 open", color: "var(--accent-orange)" },
  { label: "Deployments", value: "28", change: "2 today", color: "var(--accent-green)" },
];

const ACTIVITIES = [
  { time: "2 min ago", text: "PRD generated for \"User Auth Flow\"", type: "prd" },
  { time: "15 min ago", text: "3 JIRA tickets created for payment module", type: "jira" },
  { time: "1 hr ago", text: "Deploy #42 succeeded — staging", type: "deploy" },
  { time: "2 hrs ago", text: "QA passed for search feature", type: "qa" },
  { time: "3 hrs ago", text: "Feature spec: Dashboard Analytics", type: "feature" },
];

function DashboardPage() {
  const [apiMessage, setApiMessage] = useState("");
  const [apiLoading, setApiLoading] = useState({ hi: false, echo: false });
  const [apiStatus, setApiStatus] = useState({ hi: null, echo: null });

  const testApi = async (type) => {
    setApiLoading((prev) => ({ ...prev, [type]: true }));
    try {
      const url = type === "hi" ? `${API_BASE_URL}/hi` : `${API_BASE_URL}/echo/Akshay`;
      const res = await axios.get(url);
      setApiMessage(res.data.message);
      setApiStatus((prev) => ({ ...prev, [type]: "online" }));
    } catch {
      setApiStatus((prev) => ({ ...prev, [type]: "error" }));
      setApiMessage("API call failed");
    } finally {
      setApiLoading((prev) => ({ ...prev, [type]: false }));
    }
  };

  return (
    <>
      {/* Stat Cards */}
      <div className="stats-grid">
        {STATS.map((stat) => (
          <div className="stat-card" key={stat.label}>
            <div className="stat-indicator" style={{ background: stat.color }}></div>
            <div className="stat-body">
              <span className="stat-label">{stat.label}</span>
              <span className="stat-value">{stat.value}</span>
              <span className="stat-change">{stat.change}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Pipeline Flow */}
      <div className="card">
        <div className="card-header">
          <h2>AI Pipeline Flow</h2>
          <span className="badge badge-active">Live</span>
        </div>
        <div className="pipeline">
          {PIPELINE_STEPS.map((step, i) => (
            <React.Fragment key={step.id}>
              <div className={`pipeline-step ${step.status}`} title={step.desc}>
                <div className="step-dot">
                  {step.status === "done" && (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                  {step.status === "active" && <div className="pulse-dot"></div>}
                </div>
                <span className="step-label">{step.label}</span>
              </div>
              {i < PIPELINE_STEPS.length - 1 && (
                <div className={`pipeline-connector ${step.status === "done" ? "done" : ""}`} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* API Health + Activity */}
      <div className="two-col">
        <div className="card">
          <div className="card-header">
            <h2>API Health</h2>
          </div>
          <div className="api-list">
            <div className="api-row">
              <div className="api-info">
                <code>/api/hi</code>
                <span className={`status-dot ${apiStatus.hi || "unknown"}`}></span>
                <span className="status-text">
                  {apiStatus.hi === "online" ? "Online" : apiStatus.hi === "error" ? "Error" : "Unknown"}
                </span>
              </div>
              <button
                className="btn btn-sm"
                onClick={() => testApi("hi")}
                disabled={apiLoading.hi}
              >
                {apiLoading.hi ? "Testing..." : "Test"}
              </button>
            </div>
            <div className="api-row">
              <div className="api-info">
                <code>/api/echo</code>
                <span className={`status-dot ${apiStatus.echo || "unknown"}`}></span>
                <span className="status-text">
                  {apiStatus.echo === "online" ? "Online" : apiStatus.echo === "error" ? "Error" : "Unknown"}
                </span>
              </div>
              <button
                className="btn btn-sm"
                onClick={() => testApi("echo")}
                disabled={apiLoading.echo}
              >
                {apiLoading.echo ? "Testing..." : "Test"}
              </button>
            </div>
            {apiMessage && (
              <div className="api-response">
                <span className="response-label">Response:</span>
                <code>{apiMessage}</code>
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Recent Activity</h2>
          </div>
          <div className="activity-list">
            {ACTIVITIES.map((item, i) => (
              <div className="activity-item" key={i}>
                <div className={`activity-dot ${item.type}`}></div>
                <div className="activity-body">
                  <span className="activity-text">{item.text}</span>
                  <span className="activity-time">{item.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

function PipelinePage() {
  return (
    <div className="card">
      <div className="card-header">
        <h2>Pipeline Management</h2>
        <span className="badge">Coming Soon</span>
      </div>
      <div className="empty-state">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
          <line x1="6" y1="3" x2="6" y2="15" /><circle cx="18" cy="6" r="3" /><circle cx="6" cy="18" r="3" /><path d="M18 9a9 9 0 0 1-9 9" />
        </svg>
        <p>AI-driven pipeline management will be available here.</p>
        <p className="sub-text">Prompt &rarr; PRD &rarr; Feature &rarr; JIRA &rarr; Dev &rarr; QA &rarr; Deploy</p>
      </div>
    </div>
  );
}

function ApisPage() {
  const [message, setMessage] = useState("");

  const getHi = async () => {
    const res = await axios.get(`${API_BASE_URL}/hi`);
    setMessage(res.data.message);
  };

  const getEcho = async () => {
    const res = await axios.get(`${API_BASE_URL}/echo/Akshay`);
    setMessage(res.data.message);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>API Testing</h2>
      </div>
      <div className="api-test-section">
        <div className="api-test-row">
          <div>
            <h3>GET /api/hi</h3>
            <p className="sub-text">Returns a greeting message from the server</p>
          </div>
          <button className="btn" onClick={getHi}>Say Hi</button>
        </div>
        <div className="api-test-row">
          <div>
            <h3>GET /api/echo/Akshay</h3>
            <p className="sub-text">Echoes back the given name parameter</p>
          </div>
          <button className="btn" onClick={getEcho}>Echo</button>
        </div>
        {message && (
          <div className="api-response">
            <span className="response-label">Response:</span>
            <code>{message}</code>
          </div>
        )}
      </div>
    </div>
  );
}

function SettingsPage() {
  return (
    <div className="card">
      <div className="card-header">
        <h2>Settings</h2>
        <span className="badge">Coming Soon</span>
      </div>
      <div className="empty-state">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
          <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
        <p>Platform settings and configuration will be available here.</p>
      </div>
    </div>
  );
}

function Dashboard({ activePage }) {
  switch (activePage) {
    case "pipeline":
      return <PipelinePage />;
    case "apis":
      return <ApisPage />;
    case "settings":
      return <SettingsPage />;
    default:
      return <DashboardPage />;
  }
}

export default Dashboard;
