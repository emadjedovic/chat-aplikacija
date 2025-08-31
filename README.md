# Chat aplikacija

Ovo je fullstack chat projekt koji omogućava razmjenu poruka u stvarnom vremenu.  
Aplikacija se sastoji od **backend-a (FastAPI)** i **frontend-a (React)** te je upakirana u Docker za jednostavno pokretanje.

---

## 🎯 Funkcionalnosti

- Generiranje nasumičnog korisničkog imena pri ulasku u aplikaciju
- Globalni chat kanal u kojem sudjeluju svi aktivni korisnici
- Pregled aktivnih korisnika u sidebar-u
- Slanje i primanje poruka u globalnom chatu
- Obavijest kada se novi korisnik pridruži
- Privatni razgovori 1-na-1
- Notifikacije (badge) za:
  - nove privatne poruke
  - novo kreirane privatne chatove
- Automatsko označavanje poruka kao pročitanih kada se otvori chat
- Responzivan dizajn (radi i na mobitelima i tabletima)

---

## 🛠️ Tehnologije

- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Frontend:** React, React-Bootstrap
- **Realtime:** WebSocket (za privatne poruke i notifikacije)
- **Ostalo:** Docker, Axios

---
