import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import Dashboard from "./components/Dashboard";
import "./App.css";

function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("theme") || "dark";
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activePage, setActivePage] = useState("dashboard");

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("theme", next);
  };

  return (
    <div className={`app ${theme}`}>
      <Sidebar
        collapsed={sidebarCollapsed}
        activePage={activePage}
        onNavigate={setActivePage}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div className={`main-area ${sidebarCollapsed ? "collapsed" : ""}`}>
        <TopBar theme={theme} onToggleTheme={toggleTheme} />
        <div className="page-content">
          <Dashboard activePage={activePage} />
        </div>
      </div>
    </div>
  );
}

export default App;
