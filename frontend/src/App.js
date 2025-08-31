import React, { useState, useEffect, useRef } from "react";
import { Container, Row, Col, Button } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import axios from "axios";
import { Sidebar } from "./components/Sidebar";
import { GlobalChat } from "./components/GlobalChat";
import { PrivateChat } from "./components/PrivateChat";
import "./css/index.css";
import "./css/globalChat.css";

export const App = () => {
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [input, setInput] = useState("");

  const [activePrivateChat, setActivePrivateChat] = useState(null);
  const [messageCache, setMessageCache] = useState({}); // mapa chat_id -> poruke
  const [privateWS, setPrivateWS] = useState(null);
  const [unreadBadges, setUnreadBadges] = useState({}); // { other_user_id: true } znaci ima neprocitanih poruka
  const hasJoined = useRef(false);

  useEffect(() => {
    async function generateUsernameAndJoin() {
      if (hasJoined.current) return; // <-- sprjecava duplikaciju
      hasJoined.current = true;

      try {
        const responseUsername = await axios.get(
          "http://localhost:8000/generate-username"
        );
        const generatedUsername = responseUsername.data.username;

        const responseUser = await axios.post("http://localhost:8000/join", {
          username: generatedUsername,
        });

        setUser(responseUser.data);
      } catch (error) {
        console.error("Error setting up user:", error);
      }
    }

    generateUsernameAndJoin();
  }, []);

  // --- polling za globalne poruke ---
  useEffect(() => {
    if (!user || activePrivateChat) return; // ne radimo polling za globalni chat ukoliko je user otvorio neki privatni chat
    const intervalTime = 2000 + Math.random() * 3000; // 2-5s

    const pollMessages = setInterval(async () => {
      try {
        const responseMessages = await axios.get(
          `http://localhost:8000/messages/unread?user_id=${user.id}`
        );
        const data = responseMessages.data; // niz
        if (data && Array.isArray(data)) {
          setMessages((prev) => [...prev, ...data]);
        }
      } catch (err) {
        console.error("Message polling error:", err);
      }
    }, intervalTime);
    return () => clearInterval(pollMessages);
  }, [user, activePrivateChat]);

  // --- polling za aktivne korisnike ---
  useEffect(() => {
    if (!user) return;
    const intervalTime = 5000 + Math.random() * 5000; // 5-10s

    const pollActiveUsers = setInterval(async () => {
      try {
        const responseUsers = await axios.get(
          `http://localhost:8000/users/active?current_user_id=${user.id}`
        );
        setUsers(responseUsers.data);
      } catch (err) {
        console.error("User polling error:", err);
      }
    }, intervalTime);
    return () => clearInterval(pollActiveUsers);
  }, [user, activePrivateChat]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    try {
      const newMessage = {
        content: input,
        username: user.username,
        type: "user_message",
        user_id: user.id,
      };
      const response = await axios.post(
        "http://localhost:8000/messages",
        newMessage
      );
      setMessages((prev) => [...prev, response.data]);
      setInput("");
    } catch (err) {
      console.error("Send message error:", err);
    }
  };

  // skenira notifikacije kako bi postavili badgeve
  useEffect(() => {
    if (!user) return;
    const fetchUnreadBadges = async () => {
      try {
        const res = await axios.get(
          `http://localhost:8000/notifications/unread?current_user_id=${user.id}`
        );
        setUnreadBadges(res.data || {});
      } catch (err) {
        console.error("Unread badges error:", err);
      }
    };

    fetchUnreadBadges();
  }, [user]);

  useEffect(() => {
    if (!user) return;
    const ws = new WebSocket("ws://localhost:8000/chats/ws");

    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "connect", user_id: user.id }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "new_message") {
        const m = msg.data;
        setMessageCache((prev) => ({
          ...prev,
          [m.chat_id]: [...(prev[m.chat_id] || []), m],
        }));
        // ako je otvoren globalni chat ili trenutni privatni chat nije onaj u koji je stigla nova poruka
        if (!activePrivateChat || activePrivateChat.id !== m.chat_id) {
          setUnreadBadges((prev) => ({ ...prev, [m.sender_id]: true }));
        }
        return;
      }

      if (msg.type === "notification") {
        const { notification_type, chat_id, sender_id, other_user_id } =
          msg.data;
        const who = sender_id ?? other_user_id;
        if (who && (!activePrivateChat || activePrivateChat.id !== chat_id)) {
          setUnreadBadges((prev) => ({ ...prev, [who]: true }));
        }
        return;
      }
    };

    ws.onclose = () => {};
    setPrivateWS(ws);
    return () => {
      ws.close();
      setPrivateWS(null);
    };
  }, [user, activePrivateChat?.id]);

  const openPrivateChat = async (otherUser) => {
    if (!user) return;
    try {
      const res = await axios.post("http://localhost:8000/chats", {
        user1_id: user.id,
        user2_id: otherUser.id,
      });

      const chat = res.data;

      if (chat?.id && !messageCache[chat.id]) {
        const msgRes = await axios.get(
          `http://localhost:8000/chats/${chat.id}/messages`
        );
        setMessageCache((prev) => ({ ...prev, [chat.id]: msgRes.data }));
      }

      // oznaciti notifikacije kao procitane
      await axios.patch(`http://localhost:8000/notifications/${chat.id}/read`, {
        user_id: user.id,
      });

      setUnreadBadges((prev) => {
        const next = { ...prev };
        delete next[otherUser.id];
        return next;
      });

      setActivePrivateChat(chat);
    } catch (err) {
      console.error("Error opening private chat:", err);
    }
  };

  const sendPrivateMessage = (text) => {
    if (!text.trim() || !activePrivateChat || !privateWS) return;

    const msg = {
      chat_id: activePrivateChat.id,
      sender_id: user.id,
      content: text,
      created_at: new Date().toISOString(),
      type: "user_message",
    };

    privateWS.send(JSON.stringify({ type: "new_message", data: msg }));

    setMessageCache((prev) => ({
      ...prev,
      [activePrivateChat.id]: [...(prev[activePrivateChat.id] || []), msg],
    }));
  };

  return (
    <Container fluid className="mt-4">
      {user ? (
        <Row>
          <Col sm={4} md={4} xl={3} className="px-1">
            <p>
              <i>Korisničko ime: {user.username}</i>
            </p>
            <Sidebar
              users={users}
              user={user}
              unreadBadges={unreadBadges}
              onUserSelect={openPrivateChat}
            />
          </Col>
          <Col sm={8} md={8} xl={9} className="px-1">
            {activePrivateChat ? (
              <>
                <Button
                  variant="dark"
                  size="sm"
                  className="mb-2"
                  onClick={() => setActivePrivateChat(null)}
                >
                  Nazad na globalni chat
                </Button>
                <PrivateChat
                  activeChat={activePrivateChat}
                  messageCache={messageCache}
                  sendMessage={sendPrivateMessage}
                  user={user}
                />
              </>
            ) : (
              <GlobalChat
                messages={messages}
                input={input}
                setInput={setInput}
                sendMessage={sendMessage}
                user={user}
              />
            )}
          </Col>
        </Row>
      ) : (
        <p>Generisanje korisničkog imena...</p>
      )}
    </Container>
  );
};
