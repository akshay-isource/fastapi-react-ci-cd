import React, { useState } from "react";
import axios from "axios";

function App() {
  const [message, setMessage] = useState("");

  const getHi = async () => {
    const res = await axios.get("http://127.0.0.1:8000/hi");
    setMessage(res.data.message);
  };

  const getEcho = async () => {
    const res = await axios.get("http://127.0.0.1:8000/echo/Akshay");
    setMessage(res.data.message);
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>FastAPI + React Demo</h2>

      <button onClick={getHi}>Say Hi</button>
      <button onClick={getEcho} style={{ marginLeft: "10px" }}>
        Echo
      </button>

      <p>{message}</p>
    </div>
  );
}

export default App;
