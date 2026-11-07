# TorDirect on Arch Linux / Omarchy

This document provides setup instructions for running TorDirect on Arch Linux or Omarchy-based distributions. For general usage and command reference, see the main [README](README.md).

## 1. Installing Tor and Required Tools

Install Tor from the official Arch repositories:

```bash
sudo pacman -S tor
```

The `obfs4proxy` tool, required for obfuscated bridges (to bypass censorship and filtering), is available in the AUR. Install it using your preferred AUR helper:

```bash
# Using yay
yay -S obfs4proxy

# Or manually with makepkg
cd /tmp
git clone https://aur.archlinux.org/obfs4proxy.git
cd obfs4proxy
makepkg -si
```

> **Note for other distributions:**
> - **Ubuntu / Debian:** `sudo apt install tor obfs4proxy`
> - **Fedora:** `sudo dnf install tor obfs4proxy`
> - **NixOS:** Use the `tor` module and enable the `obfs4proxy` option.

## 2. Tor Configuration

The main Tor configuration file is located at `/etc/tor/torrc`. Edit it with your preferred editor (e.g., `nano` or `vim`) and add or modify the following lines:

```ini
# Enable SOCKS5 proxy on 127.0.0.1:9050
SocksPort 127.0.0.1:9050

# Enable ControlPort for applications like TorDirect
ControlPort 127.0.0.1:9051

# Use cookie-based authentication (default in Arch Linux)
CookieAuthentication 1
CookiePath /run/tor-control/control_auth_cookie

# Enable use of bridges
UseBridges 1

# Specify obfuscated transport plugin
ClientTransportPlugin obfs4 exec obfs4proxy

# !!! WARNING: Bridge addresses must be obtained from valid sources !!!
# Obtain obfs4 bridge addresses from obfs4bridges.torproject.org
# and add them below. Do not copy the example addresses directly.
# Example format (replace with your actual bridges):
# Bridge obfs4 192.0.2.1:443 "ABCD1234" "EFGH5678"
```

> **Important:** Bridge addresses must be retrieved from trusted sources. The addresses listed here are only examples and must not be used literally.

## 3. Systemd Override for Arch Linux

Arch Linux's `tor.service` runs with `ProtectSystem=full`, which can prevent writing the cookie file. Create an override directory and file:

```bash
sudo mkdir -p /etc/systemd/system/tor.service.d
```

Create the override configuration file:

```bash
sudo tee /etc/systemd/system/tor.service.d/override.conf > /dev/null << 'EOF'
[Service]
ReadWritePaths=/run/tor-control
EOF
```

Reload systemd and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart tor.service
```

## 4. Enabling and Starting the Service

Enable Tor to start at boot and launch it immediately:

```bash
sudo systemctl enable --now tor.service
```

Check the service status:

```bash
sudo systemctl status tor.service
```

View real-time logs while waiting for Bootstrap to complete:

```bash
journalctl -u tor.service -f
```

Wait until Bootstrap reaches 100%.

## 5. Cookie Access Permissions

The cookie file is stored at `/run/tor-control/control_auth_cookie`. Ensure your user can read it (avoid using `chmod 777`):

```bash
sudo chown $USER:$USER /run/tor-control/control_auth_cookie
```

Or set standard read permissions:

```bash
sudo chmod 644 /run/tor-control/control_auth_cookie
```

## 6. Verifying Connectivity and Correct Operation

Run the following checks to confirm Tor is working properly:

```bash
systemctl status tor.service
```

```bash
ss -lntp | grep -E '9050|9051'
```

```bash
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip
```

Expected JSON output:

```json
{"IsTor": true, "IP": "..."}
```

If the JSON above appears, Tor has been successfully and correctly configured.

## 7. Troubleshooting

Common issues and their resolutions:

1. **Read-only file system when creating Cookie**: Ensure the systemd override (`ReadWritePaths=/run/tor-control`) is created and the service has been restarted.
2. **Permission Denied for Cookie**: Fix permissions using `chown` or `chmod 644` as shown above.
3. **obfs4proxy not found**: Confirm that `obfs4proxy` is installed from the AUR and is in your PATH.
4. **ControlPort connection error**: Restart Tor and verify that your firewall (`ufw` or `nftables`) is not blocking port 9051.
5. **Bootstrap stuck at low percentages**: Check logs (`journalctl -u tor.service`) and verify that bridge addresses are correct and obtainable.
6. **Bridges disabled**: Ensure the lines `UseBridges 1` and `ClientTransportPlugin obfs4 exec obfs4proxy` are present and uncommented in `/etc/tor/torrc`.

> **Distribution notes:** On distributions that use `apt` (e.g., Ubuntu, Debian), the service management and package names may differ slightly. The general concepts of Cookie authentication, bridges, and systemd overrides apply, but consult your dist's documentation for exact commands.

---

For general usage, commands, and project information, refer to the main [README](README.md).