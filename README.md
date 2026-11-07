<div align="center">

<img src="/logo.png" width="250" height="auto">

# TorDirect

**Secure, Serverless, Peer-to-Peer Terminal Chat over Tor v3 Onion Services**

*Built with Python, Textual, and End-to-End Encryption (E2EE).*

</div>

---


## 📦 Installation

```bash
pip install tor_direct
```

see [setup](/SETUP.md).

---


## 🛠️ Features

- **End-to-End Encryption (E2EE):** ChaCha20-Poly1305 with X25519 key exchange
- **Zero IP Leakage:** All traffic routed through Tor SOCKS5 proxy
- **Persistent Ephemeral Services:** Long-lived multiplexed connections
- **RAM-Only History:** Chat histories cleared on exit
- **Multiple Profiles:** Run isolated instances concurrently

---


## 💻 Usage & Commands

### Interactive TUI Chat

```bash
tor_direct chat
```

With a custom profile and port:

```bash
tor_direct --profile alice -p 5666
```

#### Keyboard Shortcuts

- **`q`:** Safe and clean exit
- **`a`:** Add a new peer contact (56-character onion hash)
- **`Ctrl + P`:** Open Command Palette to copy Onion ID or manage peers

### CLI Subcommands

- **Display Local Onion ID:**

  ```bash
  tor_direct id --copy
  ```

- **Contact Management:**

  ```bash
  tor_direct contact add alice <56-char-onion-hash>
  ```

  ```bash
  tor_direct contact list
  ```

  ```bash
  tor_direct contact remove alice
  ```

- **Headless Listener (Daemon mode):**

  ```bash
  tor_direct listen -p 5666 --tor-password "your_password"
  ```

- **One-shot CLI Message Send:**

  ```bash
  tor_direct send <onion-address-or-alias> "Hello over Tor E2EE!"
  ```

---


## 📄 Setup Documentation

A dedicated setup guide is available for Arch Linux / Omarchy users:

- **Install Tor and required tools**
- **Configure Tor** with obfuscated bridges (obfs4)
- **Systemd override** for cookie file permissions
- **Start and verify** the service
- **Troubleshoot** common issues

See the [setup](setup) file for complete instructions.

---


## 🔒 Security Architecture

- **End-to-End Encryption (E2EE):** Ephemeral X25519 Diffie-Hellman key exchange, HKDF key derivation, and ChaCha20-Poly1305 AEAD authenticated encryption.
- **Zero IP Leakage:** All network traffic is exclusively routed through the Tor SOCKS5 proxy.
- **Persistent Ephemeral Services:** Long-lived multiplexed connections with heartbeat/ping-pong checks.
- **RAM-Only History:** Chat histories are stored purely in memory and cleared upon exit. Only identity keys and contacts are safely persisted to disk with strict `0600` file permissions.

---


<div align="center">

**[← Back to Top](#)**

</div>