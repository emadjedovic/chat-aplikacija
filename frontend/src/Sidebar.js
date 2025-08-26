import React from "react";
import { Col } from "react-bootstrap";

export const Sidebar = ({ users }) => {
  return (
    <Col md={4}>
      <h3>Active Users</h3>
      {users ? (
        <ul>
          {users.map(u => (
            <li key={u.id}>
              {u.username} {u.joined_recently ? "(joined recently)" : ""}
            </li>
          ))}
        </ul>
      ) : (
        <p>Loading active users...</p>
      )}
    </Col>
  );
};
