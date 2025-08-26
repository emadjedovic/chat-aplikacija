// App.js
import React, { useState, useEffect } from "react";
import { Container, Row, Col } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import axios from "axios";
import { Sidebar } from "./Sidebar";
import { GlobalChat } from "./GlobalChat";

export const App = () => {
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [input, setInput] = useState("");

  useEffect(() => {
    async function generateUsernameAndJoin() {
      try {
        const response = await axios.get(
          "http://localhost:8000/generate-username"
        );
        const generatedUsername = response.data;
        console.log(generatedUsername);
        const responseUser = await axios.post(
          `http://localhost:8000/join?username=${generatedUsername}`
        );
        setUser(responseUser.data);
      } catch (error) {
        console.error("Error setting up user:", error);
      }
    }
    generateUsernameAndJoin();
  }, []);

  // --- Polling for messages ---
  useEffect(() => {
    if (!user) return;
    const intervalTime = 2000 + Math.random() * 3000;

    const pollMessages = setInterval(async () => {
      try {
        const res = await fetch(
          `http://localhost:8000/messages/new?user_id=${user.id}`
        );
        const data = await res.json();
        if (data && Array.isArray(data)) {
          setMessages((prev) => [...prev, ...data]);
        }
      } catch (err) {
        console.error("Message polling error:", err);
      }
    }, intervalTime);
    return () => clearInterval(pollMessages);
  }, [user]);

  // --- Polling for active users ---
  useEffect(() => {
    if (!user) return;
    const intervalTime = 5000 + Math.random() * 5000;

    const pollActiveUsers = setInterval(async () => {
      try {
        const res = await fetch(
          `http://localhost:8000/active-users?current_user_id=${user.id}`
        );
        const data = await res.json();
        setUsers(data);
      } catch (err) {
        console.error("User polling error:", err);
      }
    }, intervalTime);
    return () => clearInterval(pollActiveUsers);
  }, [user]);

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
    <Container fluid className="mt-4">
      {user ? (
        <Row>
          <Col sm={5} md={4} xl={3}>
            <Sidebar users={users} />
          </Col>
          <Col sm={7} md={8} xl={9}>
            <GlobalChat
              messages={messages}
              input={input}
              setInput={setInput}
              sendMessage={sendMessage}
            />
          </Col>
        </Row>
      ) : (
        <p>Generating username...</p>
      )}
    </Container>
  );
};
