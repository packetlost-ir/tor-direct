<div align="center">

# 🧅 T0rd (Tortalk)

**Secure, Serverless, Peer-to-Peer Terminal Chat over Tor v3 Onion Services**  
*Built with Python, Textual, and End-to-End Encryption (E2EE).*

[![PyPI version](https://img.shields.io/pypi/v/t0rd.svg?style=flat-square)](https://pypi.org/project/t0rd/)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

---

> *"Absolute privacy, zero metadata leakage, directly from your terminal."*

</div>

---

## 📸 Preview

<!-- 
Example of how to add a screenshot image later:
<div align="center">
  <img src="https://raw.githubusercontent.com/username/t0rd/main/docs/screenshot.png" alt="T0rd TUI Preview" width="800">
</div>
-->

```text
┌─────────────────────────────────────────────────────────────┐
│ 🧅 T0rd Chat                                                │
├─────────────────┬───────────────────────────────────────────┤
│ CONTACTS        │ Chat: alice [E2EE Secured]                │
│                 │                                           │
│ ● alice         │ You                                       │
│ ○ bob           │ Hello over Tor v3 onion service!          │
│                 │ 14:05                                     │
│                 │                                           │
│                 │ alice                                     │
│                 │ Secure and encrypted connection active.   │
│                 │ 14:06                                     │
│                 │                                           │
│                 │ Type message...                           │
└─────────────────┴───────────────────────────────────────────┘
```

---

## 📦 Installation from PyPI

T0rd is available on PyPI. You can install it directly via pip:

```bash
pip install t0rd
```

---

## 🛠️ System Requirements & Prerequisites

For T0rd to run successfully on any target machine, ensure the following requirements are met:

### 1. Tor Daemon Configuration
T0rd communicates directly with the local Tor daemon via the ControlPort and SOCKS5 proxy.
- **Tor Service:** Must be installed and actively running on the system.
- **Ports (`/etc/tor/torrc`):**
  ```text
  SocksPort 9050
  ControlPort 9051
  ```
- **Authentication:** By default, T0rd relies on Tor cookie authentication or no-password control access. If your Tor daemon requires a password, supply it via the `--tor-password` flag.

### 2. System Environment
- **Python:** Version `3.10` or higher.
- **Clipboard Utility (Optional):** For copying Onion IDs (`xclip` or `xsel` on Linux environments).

---

## 🚀 Installation

Clone the repository and install it inside a virtual environment:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install package and dependencies in editable mode
pip install --editable .
```

---

## 💻 Usage & Commands

T0rd supports multiple profiles to run isolated instances concurrently.

### 1. Interactive TUI Chat
Launch the terminal UI:
```bash
t0rd chat
```
With a custom profile and custom port:
```bash
t0rd --profile alice -p 5666
```

#### TUI Keyboard Shortcuts:
- **`q`**: Safe and clean exit.
- **`a`**: Add a new peer contact (56-character onion hash).
- **`Ctrl + P`**: Open Command Palette to copy your Onion ID or manage peers.

---

### 2. CLI Subcommands

- **Display Local Onion ID:**
  ```bash
  t0rd id --copy
  ```

- **Contact Management:**
  ```bash
  # Add contact
  t0rd contact add alice <56-char-onion-hash>

  # List contacts
  t0rd contact list

  # Remove contact
  t0rd contact remove alice
  ```

- **Headless Listener (Daemon mode):**
  ```bash
  t0rd listen -p 5666 --tor-password "your_password"
  ```

- **One-shot CLI Message Send:**
  ```bash
  t0rd send <onion-address-or-alias> "Hello over Tor E2EE!"
  ```

---

## 🔒 Security Architecture

- **End-to-End Encryption (E2EE):** Ephemeral X25519 Diffie-Hellman key exchange, HKDF key derivation, and ChaCha20-Poly1305 AEAD authenticated encryption.
- **Zero IP Leakage:** All network traffic is exclusively routed through the Tor SOCKS5 proxy.
- **Persistent Ephemeral Services:** Long-lived multiplexed connections with heartbeat/ping-pong checks.
- **RAM-Only History:** Chat histories are stored purely in memory and cleared upon exit. Only identity keys and contacts are safely persisted to disk with strict `0600` file permissions.

