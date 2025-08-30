import React from "react";
import { Container, Card, ListGroup, Dropdown } from "react-bootstrap";

export const Sidebar = ({ users, user, unreadFlags, onUserSelect }) => {
  return (
    <Container className="px-0">
      {/* Potpuni ispis u sidebar-u za sm i veće ekrane */}
      <Card className="d-none d-sm-block mt-5">
        <Card.Header style={{ backgroundColor: "black", color: "white" }}>
          Aktivni korisnici
        </Card.Header>
        <Card.Body className="p-0">
          {users.length > 0 ? (
            <ListGroup className="overflow-auto" style={{ maxHeight: "70vh" }}>
              {users
                .filter((u) => u.id !== user.id) // ne vidimo sebe u listi aktivnih
                .map((u) => (
                  <ListGroup.Item
                    key={u.id}
                    action
                    onClick={() => onUserSelect(u)}
                  >
                    {u.username}
                    {u.joined_recently && (
                      <span className="badge bg-success ms-2">novi</span>
                    )}
                    {unreadFlags[u.id] && (
                      <span className="badge-dot"></span>
                    )}
                  </ListGroup.Item>
                ))}
            </ListGroup>
          ) : (
            <p className="m-3">Učitavanje korisnika...</p>
          )}
        </Card.Body>
      </Card>

      {/* Za ekrane manje od sm prikazujemo dropdown */}
      <Dropdown className="d-block d-sm-none mt-2">
        <Dropdown.Toggle variant="dark" id="dropdown-users">
          Aktivni korisnici
        </Dropdown.Toggle>
        <Dropdown.Menu style={{ maxHeight: "50vh", overflowY: "auto" }}>
          {users.length > 0 ? (
            users
              .filter((u) => u.id !== user.id)
              .map((u) => (
                <Dropdown.Item key={u.id} onClick={() => onUserSelect(u)}>
                  {u.username}
                  {u.joined_recently && (
                    <span className="badge bg-success ms-2">novi</span>
                  )}
                </Dropdown.Item>
              ))
          ) : (
            <Dropdown.Item disabled>Učitavanje korisnika...</Dropdown.Item>
          )}
        </Dropdown.Menu>
      </Dropdown>
    </Container>
  );
};
