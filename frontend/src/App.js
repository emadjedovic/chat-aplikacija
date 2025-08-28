// App.js
import React, { useState, useEffect, useRef } from "react";
import { Container, Row, Col } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import axios from "axios";
import { Sidebar } from "./Sidebar";
import { GlobalChat } from "./GlobalChat";
import "./index.css";
import "./globalChat.css";

export const App = () => {
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [input, setInput] = useState("");
  const hasJoined = useRef(false);

  useEffect(() => {
    async function generateUsernameAndJoin() {
      if (hasJoined.current) return; // <-- prevents double run
      hasJoined.current = true;

      try {
        const responseUsername = await axios.get(
          "http://localhost:8000/generate-username"
        );
        const generatedUsername = responseUsername.data.username;

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
    if (!user) return;
    const intervalTime = 2000 + Math.random() * 3000; // 2-5s

    const pollMessages = setInterval(async () => {
      try {
        const responseMessages = await axios.get(
          `http://localhost:8000/messages/new?user_id=${user.id}`
        );
        const data = responseMessages.data; // an array
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
    const intervalTime = 5000 + Math.random() * 5000; // 5-10s

    const pollActiveUsers = setInterval(async () => {
      try {
        const responseUsers = await axios.get(
          `http://localhost:8000/active-users?current_user_id=${user.id}`
        );
        setUsers(responseUsers.data);
      } catch (err) {
        console.error("User polling error:", err);
      }
    }, intervalTime);
    return () => clearInterval(pollActiveUsers);
  }, [user]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    try {
      const newMessage = {
        content: input,
        username: user.username,
        type: "user_message",
        user_id: user.id,
      };
      const response = await axios.post(
        "http://localhost:8000/send",
        newMessage
      );
      setMessages((prev) => [...prev, response.data]);
      setInput("");
    } catch (err) {
      console.error("Send message error:", err);
    }
  };

  return (
    <Container fluid className="mt-4">
      {user ? (
        <Row>
          <Col sm={4} md={4} xl={3} className="px-1">
            <p>
              <i>Username: {user.username}</i>
            </p>
            <Sidebar users={users} />
          </Col>
          <Col sm={8} md={8} xl={9} className="px-1">
            <GlobalChat
              messages={messages}
              input={input}
              setInput={setInput}
              sendMessage={sendMessage}
              user={user}
            />
          </Col>
        </Row>
      ) : (
        <p>Generating username...</p>
      )}
    </Container>
  );
};
