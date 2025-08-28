import React from "react";
import "./globalChat.css";

export const MessageBubble = ({ message, isCurrentUser }) => {
  if (message.type === "system") {
    return (
      <div className="system-message" key={message.id}>
        {message.content}
      </div>
    );
  }

  return (
    <div className="message-row">
      <div
        className={
          isCurrentUser ? "current-user-message" : "other-user-message"
        }
      >
        <div className="message-username">{message.username}</div>
        <div>{message.content}</div>
        <div className="message-time">
          {new Date(message.created_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};
