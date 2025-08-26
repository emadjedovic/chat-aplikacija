import React from "react";
import { Container, Row, Col } from "react-bootstrap";

export const GlobalChat = ({ messages, input, setInput, sendMessage }) => {
  // {content, username, type, user_id, id, created_at}
  return (
    <Container>
      <h3>Global Chat</h3>

      {messages ? (
        <div>
          {messages.map((m) => (
            // is type is system style gray, else style in color
            <div key={m.id}>
              {m.created_at} <br></br>
              {m.username}
              <br></br>
              {m.content}
              <br></br>
            </div>
          ))}
          <div>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </div>
      ) : (
        <p>Loading Messages...</p>
      )}
    </Container>
  );
};
