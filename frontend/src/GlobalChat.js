import React, { useEffect, useRef } from "react";
import { Container, Row, Col, Form, Button } from "react-bootstrap";
import { MessageBubble } from "./MessageBubble";
import "./globalChat.css";

export const GlobalChat = ({ messages, input, setInput, sendMessage, user }) => {
  const chatEndRef = useRef(null);

  // scroll do dna kad se klikne dugme za isto
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <Container fluid className="p-3">
      <h3 className="text-center mb-4">Global Chat</h3>

      {messages.length > 0 ? (
        <div className="chat-container">
        {messages.map((m) => (
          <MessageBubble
            key={m.id}
            message={m}
            isCurrentUser={user && m.user_id === user.id}
          />
        ))}
        <div ref={chatEndRef} />
      </div>
      ) : (
        <p>Loading Messages...</p>
      )}

      {/* Button to scroll down */}
      <Row className="mt-2 mb-3">
        <Col className="d-grid">
          <Button variant="secondary" onClick={scrollToBottom}>
            Scroll to Bottom
          </Button>
        </Col>
      </Row>

      <Row className="mt-3">
        <Col xs={9}>
          <Form.Control
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
          />
        </Col>
        <Col xs={3} className="d-grid">
          <Button variant="danger" onClick={sendMessage}>
            Send
          </Button>
        </Col>
      </Row>
    </Container>
  );
};
