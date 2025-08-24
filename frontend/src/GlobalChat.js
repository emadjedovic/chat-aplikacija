import React from "react";
import { Col } from "react-bootstrap";

export const GlobalChat = ({ messages, input, setInput, sendMessage }) => {
  return (
    <Col md={8}>
      <h3>Global Chat</h3>
      <div style={{ maxHeight: "400px", overflowY: "auto", marginBottom: "10px" }}>
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
  );
};
