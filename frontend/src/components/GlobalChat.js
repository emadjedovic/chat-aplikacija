import { useRef, useEffect } from "react";
import { Container, Row, Col, Form, Button } from "react-bootstrap";
import { MessageBubble } from "./MessageBubble";

export const GlobalChat = ({
  messages,
  input,
  setInput,
  sendMessage,
  user,
}) => {
  const chatEndRef = useRef(null); // za scrollanje do dna
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "auto" });
  };

  const lastMessageId = useRef(null);

  // kada stigne nova poruka ide scroll do dna
  useEffect(() => {
    if (!messages.length) return;
    const newestId = messages[messages.length - 1].id;
    if (newestId > lastMessageId.current) {
      scrollToBottom();
      lastMessageId.current = newestId;
    }
  }, [messages]);

  return (
    <Container fluid className="p-3">
      <h3 className="text-center mb-4">
        <b>Globalni Chat</b>
      </h3>

      {messages.length > 0 ? (
        <div className="chat-container">
          {messages.map((m) => {
            return (
              <MessageBubble
                key={m.id}
                message={m}
                isCurrentUser={user && m.user_id === user.id}
              />
            );
          })}
          <div ref={chatEndRef} />
        </div>
      ) : (
        <p>Učitavanje poruka...</p>
      )}

      <Row className="mt-3 align-items-start">
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
            onChange={(e) => {
              setInput(e.target.value);
              // auto-resize
              e.target.style.height = "auto"; // reset visine
              e.target.style.height = e.target.scrollHeight + "px";
            }}
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
          <Button variant="dark" onClick={sendMessage}>
            Pošalji
          </Button>
        </Col>
      </Row>
    </Container>
  );
};
