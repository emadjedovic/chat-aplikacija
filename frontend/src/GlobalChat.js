import React, { useRef, useEffect } from "react";
import { Container, Row, Col, Form, Button } from "react-bootstrap";
import { MessageBubble } from "./MessageBubble";
import { BsArrowDown } from "react-icons/bs";

export const GlobalChat = ({
  messages,
  input,
  setInput,
  sendMessage,
  user,
}) => {
  const chatEndRef = useRef(null);

  // scroll do dna kad se klikne dugme za isto
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // --- Auto scroll whenever messages change ---
  useEffect(() => {
    scrollToBottom();
  }, [messages]); // runs whenever messages array changes

  return (
    <Container fluid className="p-3">
      <h3 className="text-center mb-4">
        <b>Globalni Chat</b>
      </h3>

      {messages.length > 0 ? (
        <div className="chat-container">
          {messages.map((m) => (
            <MessageBubble
              message={m}
              isCurrentUser={user && m.user_id === user.id}
            />
          ))}
          <div ref={chatEndRef} />
        </div>
      ) : (
        <p>Učitavanje poruka...</p>
      )}

      <Row className="mt-3">
        <Col xs={4} lg={2} className="d-grid px-1">
          <Button variant="light" onClick={scrollToBottom}>
            Idi na dno
          </Button>
        </Col>
        <Col xs={6} lg={8} className="px-1 d-grid">
          <Form.Control
            as="textarea" // imamo multi-line input
            rows={1} // default jedan red slobodan
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Upiši poruku..."
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage(); // slanje poruke na enter
                // shift+enter dodaje novi red
              }
            }}
          />
        </Col>
        <Col xs={2} lg={2} className="px-1 d-grid">
          <Button variant="danger" onClick={sendMessage}>
            Pošalji
          </Button>
        </Col>
      </Row>
    </Container>
  );
};
