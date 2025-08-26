import React from "react";
import { Container, Row, Col, ListGroup, Card } from "react-bootstrap";

export const Sidebar = ({ users }) => {
  return (
    <Container>
      <Card>
        <Card.Header style={{backgroundColor:"black", color: "white"}}>
          Aktivni korisnici
        </Card.Header>
        <Card.Body className="p-0">
          {users ? (
            <ListGroup className="overflow-auto" style={{ maxHeight: "85vh" }}>
              {users.map(u => (
                <ListGroup.Item key={u.id}>
                  <span>{u.username}</span>
                  {u.joined_recently && (
                    <span className="badge bg-success">new</span>
                  )}
                </ListGroup.Item>
              ))}
            </ListGroup>
          ) : (
            <p className="m-3">Loading active users...</p>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};
