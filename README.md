# Cyberpunk Heist – Cooperative Multiplayer RPG

A 2-player cooperative heist game built for a distributed systems class. One player is the **Infiltrator** (top-down movement, interacts with the physical world) and the other is the **Hacker** (solves minigames remotely to open doors). Communication between players happens entirely through a distributed backend using **gRPC** and **RabbitMQ**.

The Infiltrator must avoid patrolling **guard robots** that sweep each level with a directional field-of-view. Getting spotted raises an alarm that disrupts the Hacker's minigame — and getting caught **three times** ends the run.

---

## Architecture

```
┌────────────────┐                        ┌───────────────────┐
│  Player 1      │◄─── gRPC :50051 ──────►│  Lobby Service    │
│  (Infiltrator) │                        │  (Sessions)       │
│  Pygame Client │◄─── gRPC :50052 ──────►├───────────────────┤
└────────────────┘                        │  Action Service   │
        ▲                                 │  (Game Logic)     │
        │         RabbitMQ (fanout)        └─────────┬─────────┘
        └─────────────────────────────────────────────┘
┌────────────────┐                                 ▲
│  Player 2      │◄─── gRPC :50051/:50052 ────────►│
│  (Hacker)      │                                 │
│  Pygame Client │◄──── RabbitMQ ──────────────────┘
└────────────────┘
```

The backend is split into independently deployable **microservices**, each with its own `.proto` definition:

| Service            | Port  | Responsibility                                                                        |
| ------------------ | ----- | ------------------------------------------------------------------------------------- |
| **Lobby Service**  | 50051 | `CreateLobby`, `JoinLobby` — matchmaking & session management                         |
| **Action Service** | 50052 | `UnlockDoor`, `DisableCamera`, `DisableLaser`, `GrantNetworkAccess` — in-game actions |

- **gRPC** – Each microservice exposes a focused set of RPCs via its own protobuf service definition.
- **RabbitMQ** – Fanout exchange broadcasts real-time events (`START_GAME`, `USB_PLUGGED`, `DOOR_HACKED`, `ALARM`, `GAME_OVER`, `GAME_WON`) to all connected clients.
- **Pygame** – Each player runs their own game window locally.

---

## Tech Stack

| Component        | Technology                            |
| ---------------- | ------------------------------------- |
| Game Client      | Python 3.11, Pygame                   |
| RPC Framework    | gRPC (protobuf)                       |
| Message Broker   | RabbitMQ 3 (AMQP)                     |
| Containerization | Docker, Docker Compose                |
| Assets           | Jerom & Kenney.nl tilesets, Kenney UI |

---

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- A virtual environment (recommended)

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd rpgGame
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the backend (RabbitMQ + gRPC microservices)

```bash
sudo docker compose up --build
```

Wait until you see the RabbitMQ health check pass, then:

- `Lobby Service is running on port 50051`
- `Action Service is running on port 50052`

### 3. Run Player 1 – Infiltrator

Open a terminal:

```bash
source .venv/bin/activate
python3.11 -m main
```

Click **HOST GAME**. A 4-character lobby code will appear (e.g. `HMZX`).

### 4. Run Player 2 – Hacker

Open a **second** terminal (same machine or another machine on the LAN):

```bash
source .venv/bin/activate
python3.11 -m main
```

Click **JOIN GAME**, type the lobby code, press **Enter**.

---

## Playing on a Local Network

By default the client connects to `localhost`. To play across two machines:

1. Run Docker on the **host machine** (the one running `docker compose up`).
2. On the **remote machine**, edit `client/game_init.py` and `rabbitmq/rabbitmq_helper.py` to replace `localhost` with the host machine's LAN IP (e.g. `192.168.1.100`):
   - `grpc.insecure_channel("192.168.1.100:50051")` (Lobby)
   - `grpc.insecure_channel("192.168.1.100:50052")` (Action)
   - `GameEventSubscriber(host="192.168.1.100")`
3. Ensure ports `5672`, `50051`, and `50052` are open on the host's firewall.

---

## How to Play

### Infiltrator (Player 1)

- **WASD** – Move around the map
- **E** – Interact with terminals (plugs USB, enabling the Hacker to open the linked door)
- Walk into **vents** to advance to the next level
- **Avoid the guard robots!** Each guard patrols the open area with a visible field-of-view cone (blocked by walls). Stepping into a cone trips the alarm. The on-screen **DETECTED x / 3** counter tracks how many times you've been spotted on the current level.

### Hacker (Player 2)

- Wait for the Infiltrator to plug USB at a terminal
- A timing minigame appears: press **Space** when the white cursor is inside the green zone
- Successfully hit **3 nodes** to unlock the door
- After unlocking, wait for the Infiltrator to find the next terminal
- If the Infiltrator is spotted, an **ALARM** fires and your hack progress is reset to zero

### Guards & Alarms

- Guards move slowly and turn at walls, sweeping a directional vision cone in their facing direction.
- Leaving and re-entering a cone re-triggers detection each time.
- The detection counter **resets at the start of every level**.
- Being detected **3 times** ends the run with a **GAME OVER** screen.
- Later levels spawn **additional guards** for increased difficulty.

### End States

- **GAME OVER** – The Infiltrator was caught three times. Press **Esc** to return to the main menu.
- **HEIST COMPLETE** – The Infiltrator reached the vent on the final level. Press **Esc** to return to the main menu.

### Game Flow (per level)

1. Infiltrator finds an accessible terminal → presses E (while dodging guards)
2. Hacker's screen activates → completes the minigame → door opens
3. Infiltrator walks through the opened door → finds the next terminal → repeat
4. Final door leads to a vent → next level loads (guards reset, an extra guard may appear)
5. Reaching the vent on the last level wins the heist

---

## Project Structure

```
├── main.py                      # Entry point: game loop & state machine
├── game_config.json             # Screen size, tile size
├── logger_config.py             # Logging setup (cross-cutting)
├── requirements.txt             # grpcio, pika, pygame
├── Dockerfile                   # Python 3.11 slim for server container
├── docker-compose.yml           # RabbitMQ + gRPC microservice containers
│
├── client/                      # Client-side game logic
│   ├── event_handler.py         # Input handling per game state
│   ├── game_init.py             # Display, gRPC client, and asset initialization
│   ├── renderer.py              # All Pygame rendering functions
│   └── utils.py                 # Config & level loading utilities
│
├── assets/                      # Pygame helper modules (code only)
│   ├── character_helper.py      # Sprite sheet manager & Player class
│   ├── tile_helper.py           # Tileset loading & slicing (with upscaling support)
│   ├── guard_helper.py          # Patrolling guard robot with FOV/line-of-sight detection
│   └── ui_helper.py             # Button widget
│
├── resources/                   # Raw data files (no Python)
│   ├── fonts/                   # Kenney Future .ttf fonts
│   ├── ui_textures/             # Kenney UI button/bar PNGs
│   ├── Jerom_topRL_CCBYSA3.png  # Active tile + guard-robot sprite sheet (16px)
│   ├── jerom_tileset_config.json # Active tile definitions (16px → 32px render)
│   ├── tilesetv1.0.png          # Legacy tile sprite sheet
│   ├── tilesetv1.0_config.json  # Legacy tile definitions
│   ├── character_maleAdventurer_sheet.png
│   └── character_maleAdventurer_sheet.xml
│
├── levels/                      # Level definitions & logic
│   ├── level_manager.py         # Map parsing, collision, door/terminal O(1) lookups
│   └── levels.json              # Level maps with terminal→door mappings & guard spawns
│
├── rabbitmq/                    # Message broker layer
│   ├── rabbit_server.py         # Publisher (server-side, runs in Docker)
│   └── rabbitmq_helper.py       # Subscriber (client-side, background thread with retry)
│
└── grpc_server/                 # gRPC microservices (run in Docker)
    ├── lobby.proto              # Protobuf definition: Lobby Service
    ├── lobby_server.py          # Lobby Service implementation (sessions)
    ├── lobby_pb2.py             # Generated protobuf code (lobby)
    ├── lobby_pb2_grpc.py        # Generated gRPC stubs (lobby)
    ├── action.proto             # Protobuf definition: Action Service
    ├── action_server.py         # Action Service implementation (game logic)
    ├── action_pb2.py            # Generated protobuf code (action)
    └── action_pb2_grpc.py       # Generated gRPC stubs (action)
```

---

## RabbitMQ Management UI

While Docker is running, visit [http://localhost:15672](http://localhost:15672) (guest/guest) to monitor exchanges, queues, and message flow in real-time.
