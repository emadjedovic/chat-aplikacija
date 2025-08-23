import React, { useState, useEffect } from "react";
import { Container, Row, Col } from "react-bootstrap";
import 'bootstrap/dist/css/bootstrap.min.css';


// integrate cache for old messages to avoid expensive database queries
// should we integrate cache in backend instead of here?
// why do we need "active" variable?

export const App = () => {
  const [username, setUsername] = useState(
    "User_" + Math.floor(Math.random() * 10000)
  );
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [input, setInput] = useState("");

  // --- Polling for messages ---
  useEffect(() => {
    let active = true;

    const pollMessages = async () => {
      if (!active) return;

      try {
        const res = await fetch("http://localhost:8000/poll-messages");
        const data = await res.json();
        if (data.message) {
          setMessages((prev) => [...prev, data.message]);
        }
      } catch (err) {
        console.error("Message polling error:", err);
      }

      // Schedule next poll with random interval 1–3s
      const interval = 1000 + Math.random() * 3000;
      setTimeout(pollMessages, interval);
    };

    pollMessages();
  }, []);

  // --- Polling for active users ---
  useEffect(() => {
    let active = true;
    const pollActiveUsers = async () => {
      if (!active) return;
      try {
        const res = await fetch("http://localhost:8000/poll-active-users");
        const data = await res.json();
        setUsers(data.users);
      } catch (err) {
        console.error("User polling error:", err);
      }
      // Schedule next poll with random interval 1–3s
      const interval = 1000 + Math.random() * 3000;
      setTimeout(pollActiveUsers, interval);
    };

    pollActiveUsers();
  }, []);

  // --- Send message ---
  const sendMessage = async () => {
    if (!input.trim()) return;

    try {
      await fetch("http://localhost:8000/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, text: input }),
      });
      setInput("");
    } catch (err) {
      console.error("Send message error:", err);
    }
  };

  return (
    <Container fluid>
      <Row>
        <Col md={4}>
          <h3>Active Users</h3>
          <ul>
            {users.map((u, i) => (
              <li key={i}>{u}</li>
            ))}
          </ul>
        </Col>

        <Col md={8}>
          <h3>Global Chat</h3>
          <div
          >
            {messages.map((msg, i) => (
              <div key={i}>{msg}</div>
            ))}
          </div>
          <div>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              style={{ width: "70%", marginRight: "5px" }}
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </Col>
      </Row>
    </Container>
  );
};
