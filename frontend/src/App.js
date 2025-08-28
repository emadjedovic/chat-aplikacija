import React, { useState, useEffect, useRef } from "react";
import { Container, Row, Col, Button } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import axios from "axios";
import { Sidebar } from "./Sidebar";
import { GlobalChat } from "./GlobalChat";
import { PrivateChat } from "./PrivateChat";
import "./index.css";
import "./globalChat.css";

export const App = () => {
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [input, setInput] = useState("");

  const [privateChats, setPrivateChats] = useState([]); // metadata for 1-1 chats
  const [activePrivateChat, setActivePrivateChat] = useState(null);
  const [messageCache, setMessageCache] = useState({}); // messages per chatId
  const [privateWS, setPrivateWS] = useState(null); // WebSocket for private chats only

  const hasJoined = useRef(false);

  useEffect(() => {
    async function generateUsernameAndJoin() {
      if (hasJoined.current) return; // <-- prevents double run
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

  // --- Polling for messages ---
  useEffect(() => {
    if (!user) return;
    const intervalTime = 2000 + Math.random() * 3000; // 2-5s

    const pollMessages = setInterval(async () => {
      try {
        const responseMessages = await axios.get(
          `http://localhost:8000/messages/new?user_id=${user.id}`
        );
        const data = responseMessages.data; // an array
        if (data && Array.isArray(data)) {
          setMessages((prev) => [...prev, ...data]);
        }
      } catch (err) {
        console.error("Message polling error:", err);
      }
    }, intervalTime);
    return () => clearInterval(pollMessages);
  }, [user]);

  // --- Polling for active users ---
  useEffect(() => {
    if (!user) return;
    const intervalTime = 5000 + Math.random() * 5000; // 5-10s

    const pollActiveUsers = setInterval(async () => {
      try {
        const responseUsers = await axios.get(
          `http://localhost:8000/active-users?current_user_id=${user.id}`
        );
        setUsers(responseUsers.data);
      } catch (err) {
        console.error("User polling error:", err);
      }
    }, intervalTime);
    return () => clearInterval(pollActiveUsers);
  }, [user]);

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
        "http://localhost:8000/send",
        newMessage
      );
      setMessages((prev) => [...prev, response.data]);
      setInput("");
    } catch (err) {
      console.error("Send message error:", err);
    }
  };

  const openPrivateWS = () => {
    if (privateWS) return; // already connected

    // Connect to the new WS path
    const ws = new WebSocket("ws://localhost:8000/chats/ws");

    ws.onopen = () => {
      console.log("Private chat WebSocket connected");

      // Send the initial connect message with user_id
      ws.send(JSON.stringify({ type: "connect", user_id: user.id }));
    };

    ws.onclose = () => console.log("Private chat WebSocket disconnected");

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "private_message") {
        const chatId = msg.data.chat_id;

        setMessageCache((prev) => ({
          ...prev,
          [chatId]: [...(prev[chatId] || []), msg.data],
        }));
      }
    };

    setPrivateWS(ws);
  };

  const openPrivateChat = async (otherUser) => {
    if (!user) return;
    openPrivateWS();

    try {
      // fetch or create chat in one call
      const res = await axios.get("http://localhost:8000/chats/get-or-create", {
        params: { user1_id: user.id, user2_id: otherUser.id },
      });

      const chat = res.data;

      // fetch messages if not cached
      if (chat?.id && !messageCache[chat.id]) {
        const msgRes = await axios.get(
          `http://localhost:8000/chats/${chat.id}/messages`
        );
        setMessageCache((prev) => ({
          ...prev,
          [chat.id]: msgRes.data,
        }));
      }

      setPrivateChats((prev) =>
        prev.some((c) => c.id === chat.id) ? prev : [...prev, chat]
      );

      setActivePrivateChat(chat);
    } catch (err) {
      console.error("Error opening private chat:", err);
    }
  };

  // --- Send private message ---
  const sendPrivateMessage = (text) => {
    if (!text.trim() || !activePrivateChat || !privateWS) return;

    const msg = {
      chat_id: activePrivateChat.id,
      sender_id: user.id,
      content: text,
    };

    privateWS.send(JSON.stringify({ type: "private_message", data: msg }));

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
              <i>Username: {user.username}</i>
            </p>
            <Sidebar users={users} user={user} onUserSelect={openPrivateChat} />
          </Col>
          <Col sm={8} md={8} xl={9} className="px-1">
            {activePrivateChat ? (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  className="mb-2"
                  onClick={() => setActivePrivateChat(null)}
                >
                  ⬅ Nazad na globalni chat
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
        <p>Generating username...</p>
      )}
    </Container>
  );
};
