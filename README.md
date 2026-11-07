<div align="center">

# 🧅 TorDirect (tor_direct)

**Secure, Serverless, Peer-to-Peer Terminal Chat over Tor v3 Onion Services**  
*Built with Python, Textual, and End-to-End Encryption (E2EE).*

[![PyPI version](https://img.shields.io/pypi/v/tor_direct.svg?style=flat-square)](https://pypi.org/project/tor_direct/)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

</div>

---

## 📸 Preview

<!-- 
Example of how to add a screenshot image later:
<div align="center">
  <img src="https://raw.githubusercontent.com/username/tor_direct/main/docs/screenshot.png" alt="TorDirect TUI Preview" width="800">
</div>
-->

```text
┌─────────────────────────────────────────────────────────────┐
│ 🧅 TorDirect Chat                                           │
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

TorDirect is available on PyPI. You can install it directly via pip:

```bash
pip install tor_direct
```

---

## 🛠️ System Requirements & Prerequisites

For TorDirect to run successfully on any target machine, ensure the following requirements are met:

### 1. نصب Tor و ابزارهای موردنیاز
برای شروع، بسته Tor را از مخازن اصلی Arch نصب کنید:
```bash
sudo pacman -S tor
```
ابزار `obfs4proxy` که مورد نیاز برای استفاده از پل‌های obfs4 (برای دوری از سنجش-filtering و censura) است، موجود در AUR است. می‌توانید آن را با یکی از.tools زیر نصب کنید:
```bash
# استفاده از yay
yay -S obfs4proxy

# یا مستقیم با makepkg
cd /tmp
git clone https://aur.archlinux.org/obfs4proxy.git
cd obfs4proxy
makepkg -si
```

### 2. پیکربندی Tor
فایل تنظیمات اصلی Tor در مسیر `/etc/tor/torrc` قرار دارد.پس از نصب، آن را با ویرایشگر علاقه‌مندی خود (مثل `nano` یا `vim`) باز کنید و پارامترهای زیر را اضافه یا تغییر دهید:

```ini
# فعال‌سازی پورت SOCKS5 برای برنامه‌های کلienta
SocksPort 127.0.0.1:9050

# فعال کردن پورت کنترل برای برنامه‌ها مثل tord
ControlPort 127.0.0.1:9051

# استفاده از احراز هویت اساسCookie (پیش‌فرض در Arch Linux)
CookieAuthentication 1
CookiePath /run/tor-control/control_auth_cookie

# فعال‌سازی استفاده از Bridge ها
UseBridges 1

# مشخص کردنtransport plugin obfs4
ClientTransportPlugin obfs4 exec obfs4proxy

# !!! WARNING: آدرس‌های زیر را باید از منابع معتبر تهیه کنید !!!
# آدرس Bridge obfs4 را از obfs4bridges.torproject.org دریافت کنید و جایگذاری کنید.
# نمونه (را کپی نکنید، فقط مثال):
# Bridge obfs4 192.0.2.1:443 "ABCD1234" "EFGH5678"
```
> **نکته مهم:** آدرس Bridge ha را نمی‌توان در اینجا ثابت کرد و کاربر باید آدرس‌های معتبر خود را از وب‌سایت Tor Project بگیرد.

### 3. اصلاح محدودیت systemd
در Arch Linux، سرویس Tor با محدودیت `ProtectSystem=full` فعال است که می‌تواند مانع نوشتن فایلCookie trởاند. برای غلبه بر این مشکل، فایل override systemd ایجاد کنید:

```bash
sudo mkdir -p /etc/systemd/system/tor.service.d
```

فایل `/etc/systemd/system/tor.service.d/override.conf` را ایجاد کنید و محتوای زیر را درج کنید:

```ini
[Service]
ReadWritePaths=/run/tor-control
```

سرویس systemd را مجدد بارگذاری کرده و سرویس را restarted کنید:
```bash
sudo systemctl daemon-reload
sudo systemctl restart tor.service
```

### 4. راه‌اندازی و فعال‌سازی سرویس
```bash
sudo systemctl enable --now tor.service
```
برای بررسی وضعیت صحیح سرویس:
```bash
sudo systemctl status tor.service
```
برای مشاهده لاگ‌های لحظه‌ای و انتظار coming Bootstrap:
```bash
journalctl -u tor.service -f
```
منتظر بمانید تا Bootstrapped به 100 درصد برسد.

### 5. بررسی دسترسیCookie
فایلCookie در مسیر `/run/tor-control/control_auth_cookie` ذخیره می‌شود. کاربر باید بتواند فایل را خوانده باشد. دسترسی‌ها را با دستور زیر اصلاح کنید (بدون استفاده از `chmod 777`):

```bash
sudo chown $USER:$USER /run/tor-control/control_auth_cookie
```
یا
```bash
sudo chmod 644 /run/tor-control/control_auth_cookie
```

### 6. بررسی اتصال و صحت عملکرد
وارد شوید و موارد زیر را اجرا کنید:

```bash
systemctl status tor.service
```

```bash
ss -lntp | grep -E '9050|9051'
```

```bash
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip
```
نتیجه مورد انتظار (JSON):
```json
{"IsTor": true, "IP": "..."}
```
اگرJSON بالا दिखाई،Tor با موفقیت و به درستی راه‌اندازی شده است.

### 7. چالش‌های رایگان و rozwiązanie (Troubleshooting)
در این بخش خطاهای رایج و روش‌های آن‌ها را مشاهده می‌کنید:

1. **Read-only file system هنگام ایجاد Cookie**: مطمئن شوید که overdose systemd (`ReadWritePaths=/run/tor-control`) ساخته شده و سرویس restart شده است.
2. **Permission Denied برای Cookie**: دسترسی فایلCookie را با دستور `chown` یا `chmod 644` اصلاح کنید.
3. **نبودن obfs4proxy**: assure که obfs4proxy از AUR نصب است و در مسیر وجود دارد.
4. **خطای اتصال به ControlPort**: Tor را restart کنید و مطمئن شوید فایروال (`ufw` یا `nftables`) پورت 9051 بسته نیست.
5. **گیر کردن Bootstrap**: لاگ‌ها (`journalctl -u tor.service`) را بررسی کنید و آدرس Bridge ها را درست بودن تایید کنید.
6. **غیرفعال بودن Bridgeها**: خط‌های `UseBridges 1` و `ClientTransportPlugin obfs4 exec obfs4proxy` در `torrc` را بررسی کنید.

---

## 🔒 Security Architecture

- **End-to-End Encryption (E2EE):** Ephemeral X25519 Diffie-Hellman key exchange, HKDF key derivation, and ChaCha20-Poly1305 AEAD authenticated encryption.
- **Zero IP Leakage:** All network traffic is exclusively routed through the Tor SOCKS5 proxy.
- **Persistent Ephemeral Services:** Long-lived multiplexed connections with heartbeat/ping-pong checks.
- **RAM-Only History:** Chat histories are stored purely in memory and cleared upon exit. Only identity keys and contacts are safely persisted to disk with strict `0600` file permissions.

---

## 💻 Usage & Commands

TorDirect supports multiple profiles to run isolated instances concurrently.

### 1. Interactive TUI Chat
Launch the terminal UI:
```bash
tor_direct chat
```
With a custom profile and custom port:
```bash
tor_direct --profile alice -p 5666
```

#### TUI Keyboard Shortcuts:
- **`q`**: Safe and clean exit.
- **`a`**: Add a new peer contact (56-character onion hash).
- **`Ctrl + P`**: Open Command Palette to copy your Onion ID or manage peers.

---

### 2. CLI Subcommands

- **Display Local Onion ID:**
  ```bash
  tor_direct id --copy
  ```

- **Contact Management:**
  # Add contact
  ```bash
  tor_direct contact add alice <56-char-onion-hash>
  ```

  # List contacts
  ```bash
  tor_direct contact list
  ```

  # Remove contact
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

---

>- **RAM-Only History:** Chat histories are stored purely in memory and cleared upon exit. Only identity keys and contacts are safely persisted to disk with strict `0600` file permissions.
## Tor Setup on Arch Linux

### 1. نصب Tor و ابزارهای موردنیاز
sudo pacman -S tor

### 2. پیکربندی Tor
sudo nano /etc/tor/torrc

### 3. اصلاح محدودیت systemd
sudo mkdir -p /etc/systemd/system/tor.service.d

### 4. راه‌اندازی سرویس
sudo systemctl enable --now tor.service
