// App.js
import React, { useState, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import axios from "axios";

import { Sidebar } from "./Sidebar";
import { GlobalChat } from "./GlobalChat";

export const App = () => {
  const [user, setUser] = useState(null)
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [input, setInput] = useState("");

  useEffect(() => {
    async function generateUsernameAndJoin() {
      try {
        const response = await axios.get("http://localhost:8000/generate-username");
        const generatedUsername = response.data.username;
        const responseUser = await axios.post("http://localhost:8000/join", {
          username: generatedUsername,
        });
        setUser(responseUser.data);
      } catch (error) {
        console.error("Error setting up user:", error);
      }
    }
    generateUsernameAndJoin();
  }, []);

  // --- Polling for messages ---
  useEffect(() => {
    let active = true;

    const pollMessages = async () => {
      if (!active) return;
      try {
        const res = await fetch("http://localhost:8000/messages/new");
        const data = await res.json();
        if (data.message) {
          setMessages((prev) => [...prev, data.message]);
        }
      } catch (err) {
        console.error("Message polling error:", err);
      }
      const interval = 1000 + Math.random() * 3000;
      setTimeout(pollMessages, interval);
    };

    pollMessages();
    return () => {
      active = false;
    };
  }, []);

  // --- Polling for active users ---
  useEffect(() => {
    let active = true;

    const pollActiveUsers = async () => {
      if (!active) return;
      try {
        const res = await fetch("http://localhost:8000/active-users");
        const data = await res.json();
        setUsers(data.users);
      } catch (err) {
        console.error("User polling error:", err);
      }
      const interval = 1000 + Math.random() * 3000;
      setTimeout(pollActiveUsers, interval);
    };

    pollActiveUsers();
    return () => {
      active = false;
    };
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;
    try {
      await fetch("http://localhost:8000/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user.username, content: input }),
      });
      setInput("");
    } catch (err) {
      console.error("Send message error:", err);
    }
  };

  return (
    <Container fluid>
      {user ? (
        <Row>
          <Sidebar users={users} />
          <GlobalChat
            messages={messages}
            input={input}
            setInput={setInput}
            sendMessage={sendMessage}
          />
        </Row>
      ) : (
        <p>Generating username...</p>
      )}
    </Container>
  );
};
