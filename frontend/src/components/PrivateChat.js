import React, { useRef, useEffect, useState } from "react";
import { Container, Row, Col, Form, Button } from "react-bootstrap";
import { MessageBubble } from "./MessageBubble";
import { BsArrowDown } from "react-icons/bs";

export const PrivateChat = ({
  activeChat,
  messageCache,
  sendMessage,
  user,
}) => {
  let chatId;
  let messages = [];

  if (activeChat && activeChat.id) {
    chatId = activeChat.id;
    messages = messageCache[chatId] || [];
  } else {
    chatId = null;
    messages = [];
  }

  const [input, setInput] = useState("");

  const chatEndRef = useRef(null);
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "auto" });
  };

  const lastMessageId = useRef(null);

  useEffect(() => {
    if (!messages.length) return;

    // optimisticne poruke nisu stigle dobiti id polje
    const newestId = messages[messages.length - 1].id || messages.length;

    if (newestId > lastMessageId.current) {
      scrollToBottom();
      lastMessageId.current = newestId;
    }
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessage(input);
    setInput("");
  };

  return (
    <Container fluid className="p-3">
      <h3 className="text-center mb-4">
        <b>
          Chat sa{" "}
          {activeChat.user1.id === user.id
            ? activeChat.user2.username
            : activeChat.user1.username}
        </b>
      </h3>

      {messages.length > 0 ? (
        <div className="chat-container">
          {messages.map((m) => (
            <MessageBubble
              key={m.id}
              message={m}
              isCurrentUser={user && m.sender_id === user.id}
            />
          ))}
          <div ref={chatEndRef} />
        </div>
      ) : (
        <p>Nema poruka.</p>
      )}

      <Row className="mt-3 align-items-start">
        <Col xs={4} lg={2} className="d-grid px-1">
          <Button variant="light" onClick={scrollToBottom}>
            <BsArrowDown /> Idi na dno
          </Button>
        </Col>
        <Col xs={6} lg={8} className="px-1 d-grid">
          <Form.Control
            as="textarea"
            rows={1}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              e.target.style.height = "auto"; // reset height
              e.target.style.height = e.target.scrollHeight + "px";
            }}
            placeholder="Upiši poruku..."
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
        </Col>
        <Col xs={2} lg={2} className="px-1 d-grid">
          <Button variant="dark" onClick={handleSend}>
            Pošalji
          </Button>
        </Col>
      </Row>
    </Container>
  );
};
