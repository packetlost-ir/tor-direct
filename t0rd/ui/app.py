import asyncio
import time
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, RichLog, ListItem, ListView, Label
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual import work
from rich.panel import Panel

from t0rd.config import DEFAULT_LOCAL_PORT, SOCKS_PORT, CONTROL_PORT, CONNECT_TIMEOUT, clean_hash, normalize_and_validate_onion
from t0rd.storage import StorageManager
from t0rd.logger import setup_logging
import logging
from t0rd.network.tor import get_controller, create_onion_service, destroy_onion_service
from t0rd.network.server import PeerServer
from t0rd.network.client import connect_peer
from t0rd.network.protocol import PeerSession, OP_CHAT, perform_protocol_handshake
from t0rd.ui.commands import T0rdCommandProvider
from t0rd.ui.modals import AddContactModal

class PeerEvent(Message):
    def __init__(self, type, peer_hash, data=None):
        self.type = type
        self.peer_hash = peer_hash
        self.data = data
        super().__init__()

class T0rdApp(App):
    TITLE = "TorDirect"
    CSS = """
    Screen { background: $surface; color: $text; }
    #main { layout: horizontal; }
    #sidebar { width: 35; background: $boost; border-right: solid $primary-background; }
    #chat { layout: vertical; }
    #chat-header { height: 3; background: $panel; padding: 1; color: $accent; }
    #chat-log { height: 1fr; background: $surface; }
    #input-box { height: 3; }
    .online { color: $success; }
    .offline { color: $text-muted; }
    .unread { color: $error; text-style: bold; }
    """

    COMMANDS = App.COMMANDS | {T0rdCommandProvider}
    BINDINGS = [("q", "quit", "Quit"), ("a", "prompt_add_contact", "Add Contact")]

    def __init__(self, initial_target=None, config_dir=None, profile=None, local_port=DEFAULT_LOCAL_PORT, socks_port=SOCKS_PORT, control_port=CONTROL_PORT, tor_password=None, timeout=CONNECT_TIMEOUT):
        super().__init__()
        setup_logging(config_dir=config_dir, profile=profile)
        self.logger = logging.getLogger("t0rd.app")
        self.logger.info("Initializing T0rdApp")
        self.storage = StorageManager(config_dir=config_dir, profile=profile)
        self.local_port, self.socks_port, self.control_port, self.tor_password, self.timeout = local_port, socks_port, control_port, tor_password, timeout
        self.profile = profile
        self.sessions = {} # hash -> PeerSession
        self.chat_buffers = {} # hash -> list
        self.unread_counts = {} # hash -> int
        self.active_peer_hash = None
        self.local_onion_hash = ""
        self.display_name = profile or ""
        self._closing = False

    def action_copy_onion_id(self) -> None:
        if self.local_onion_hash:
            try:
                import pyperclip
                pyperclip.copy(self.local_onion_hash)
                self.notify(f"Onion ID copied to clipboard: {self.local_onion_hash[:8]}...", title="T0rd Identity")
            except Exception as e:
                self.notify(f"Copy failed: {e}", severity="error")

    def action_prompt_add_contact(self) -> None:
        async def _add_contact():
            h = await self.push_screen_wait(AddContactModal())
            if not h or h == self.local_onion_hash: return
            
            alias = self.storage.find_alias_by_onion(h) or f"peer-{h[:6]}"
            self.storage.add_contact(alias, h)
            self.refresh_contacts()
            
            # Switch focus to the contact
            self.active_peer_hash = h
            self.unread_counts[h] = 0
            self.refresh_contacts()
            
            # Select in ListView
            try:
                lv = self.query_one("#contacts-list", ListView)
                for i, item in enumerate(lv.children):
                    if isinstance(item, ListItem) and item.name == h:
                        lv.index = i
                        break
            except Exception: pass
            
            if h not in self.sessions:
                self.run_worker(self._connect_to_peer(h, alias))
        
        self.run_worker(_add_contact())

    async def _connect_to_peer(self, h: str, alias: str):
        self.query_one("#chat-header", Static).update(f"Connecting to {alias} via Tor...")
        try:
            r, w = await connect_peer(h, socks_port=self.socks_port)
            key, ph, pn = await perform_protocol_handshake(r, w, self.local_onion_hash, self.display_name, True)
            await self.register_session(r, w, key, ph, pn, True)
            if h == self.active_peer_hash:
                self.query_one("#chat-header", Static).update(f"Chat: {alias} [E2EE Secured]")
        except Exception as e:
            if h == self.active_peer_hash:
                self.query_one("#chat-header", Static).update(f"Chat: {alias} (Offline)")
            self.notify(f"Failed to connect to {alias}: {e}", severity="error")

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="sidebar"):
                yield Label(" CONTACTS", classes="section-title")
                yield ListView(id="contacts-list")
            with Vertical(id="chat"):
                yield Static("Select a contact", id="chat-header")
                yield RichLog(id="chat-log", markup=True)
                yield Input(placeholder="Type message...", id="msg-input")
        yield Footer()

    async def on_mount(self):
        self.refresh_contacts()
        self.run_worker(self.start_services(), name="tor-init", exclusive=True)

    async def start_services(self):
        if getattr(self, "_services_started", False):
            return
        self._services_started = True
        
        header = self.query_one("#chat-header", Static)
        self.logger.info("Tor services startup initiated")
        
        try:
            # 1. Connecting
            header.update("[bold yellow]Connecting to Tor...[/]")
            try:
                self.controller = await asyncio.to_thread(get_controller, self.control_port, self.tor_password)
            except Exception as e:
                self.logger.error(f"Failed to connect to Tor ControlPort: {e}")
                header.update("[bold red]Connection Failed[/]")
                self.notify(f"Tor connection failed: {e}", severity="error")
                return

            # 2. Authenticating (Already done in get_controller, but let's be explicit)
            header.update("[bold yellow]Authenticating with Tor...[/]")
            if not self.controller.is_authenticated():
                try:
                    await asyncio.to_thread(self.controller.authenticate, password=self.tor_password)
                except Exception as e:
                    header.update("[bold red]Authentication Failed[/]")
                    self.notify(f"Tor auth failed: {e}", severity="error")
                    return
            self.logger.info("Tor authenticated")

            # 3. Bootstrap
            header.update("[bold yellow]Waiting for Tor bootstrap...[/]")
            from t0rd.network.tor import wait_for_bootstrap
            bootstrapped = await asyncio.to_thread(wait_for_bootstrap, self.controller, timeout=30)
            if not bootstrapped:
                self.logger.warning("Tor not fully bootstrapped, proceeding anyway")
            else:
                self.logger.info("Tor bootstrapped")
            
            # 4. Onion Service
            header.update("[bold yellow]Creating Onion Service...[/]")
            id_data = self.storage.load_identity()
            
            # Use a longer timeout for publication as it can take up to 2 mins
            try:
                if id_data:
                    self.logger.info("Restoring onion service from saved identity")
                    h, _, _ = await asyncio.to_thread(
                        create_onion_service, 
                        self.controller, 
                        self.local_port, 
                        id_data["key_type"], 
                        id_data["private_key"]
                    )
                else:
                    self.logger.info("Creating new ephemeral onion service")
                    h, t, k = await asyncio.to_thread(create_onion_service, self.controller, self.local_port)
                    self.storage.save_identity(h, t, k)
            except Exception as e:
                self.logger.error(f"Onion service creation failed: {e}")
                header.update("[bold red]Onion Service Failed[/]")
                self.notify(f"Onion failed: {e}", severity="error")
                return
            
            self.local_onion_hash = clean_hash(h)
            self.logger.info(f"Onion Service Ready: {self.local_onion_hash}")
            if not self.display_name:
                self.display_name = f"peer-{self.local_onion_hash[:6]}"
            
            # 5. Peer Server
            header.update("[bold yellow]Starting Peer Server...[/]")
            self.server = PeerServer("127.0.0.1", self.local_port, self.local_onion_hash, self.display_name, self.register_session)
            try:
                await self.server.start()
            except Exception as e:
                self.logger.error(f"PeerServer failed to start: {e}")
                header.update("[bold red]Peer Server Failed[/]")
                self.notify(f"Server failed: {e}", severity="error")
                return
            self.logger.info("Peer server listening")

            # 6. Ready
            header.update(f"[bold green]Ready:[/] {self.display_name} ({self.local_onion_hash[:8]}...)")
            self.notify("TorDirect is ready!", title="Initialization")
            self.refresh_contacts()
            
        except Exception as e:
            self.logger.error(f"Unexpected initialization error: {e}", exc_info=True)
            header.update("[bold red]Initialization Failed[/]")
            self.notify(f"Error: {e}", severity="error")
        finally:
            self._services_started_complete = True

    async def register_session(self, r, w, key, h, n, init):
        h = clean_hash(h)
        if h == self.local_onion_hash: return
        
        # Mutual Discovery
        if not self.storage.find_alias_by_onion(h):
            self.storage.add_contact(n or f"peer-{h[:6]}", h)
        elif n:
            alias = self.storage.find_alias_by_onion(h)
            if alias != n: self.storage.update_alias(alias, n)
            
        session = PeerSession(r, w, key, h, n, init, self.protocol_callback)
        self.sessions[h] = session
        session.start()
        self.post_message(PeerEvent("status", h))

    async def protocol_callback(self, type, h, data):
        self.post_message(PeerEvent(type, h, data))

    def write_message_to_log(self, sender: str, text: str, ts: str, h: str):
        log = self.query_one("#chat-log", RichLog)
        is_me = (sender == "me")
        
        if is_me:
            who = self.display_name or "You"
            bg_color = "on #2b5278"
            align_tag = "right"
        else:
            who = self.storage.find_alias_by_onion(h) or f"peer-{h[:6]}"
            bg_color = "on #182533"
            align_tag = "left"

        max_w = max(20, log.size.width - 10) if log.size.width > 15 else 50
        wrapped_lines = []
        for paragraph in text.splitlines():
            if not paragraph:
                wrapped_lines.append("")
            else:
                while len(paragraph) > max_w:
                    wrapped_lines.append(paragraph[:max_w])
                    paragraph = paragraph[max_w:]
                wrapped_lines.append(paragraph)

        lines = wrapped_lines if wrapped_lines else [""]
        max_content_len = max(len(l) for l in lines) if lines else 0
        width = max(len(who) + 2, max_content_len + 2)

        content_lines = []
        for l in lines:
            content_lines.append(f" {l.ljust(width - 1)}")
        box_str = "\n".join(content_lines)
        rendered = f"[{bg_color}]{box_str}[/]"
        
        log.write("")
        log.write(f"[{align_tag}][dim] {who} [/][/{align_tag}]")
        log.write(f"[{align_tag}]{rendered}[/{align_tag}]")
        log.write(f"[{align_tag}][dim] {ts} [/][/{align_tag}]")
        log.write("")

    def on_peer_event(self, event: PeerEvent):
        if self._closing or not self.is_mounted: return
        h = event.peer_hash
        if event.type == "chat":
            msg = {"sender": "peer", "text": event.data["m"], "ts": time.strftime("%H:%M")}
            if h not in self.chat_buffers: self.chat_buffers[h] = []
            self.chat_buffers[h].append(msg)
            
            if h == self.active_peer_hash:
                self.write_message_to_log("peer", msg["text"], msg["ts"], h)
            else:
                self.unread_counts[h] = self.unread_counts.get(h, 0) + 1
                self.notify(f"New message from {h[:6]}")
                self.refresh_contacts()
        elif event.type in ("status", "closed"):
            if event.type == "closed": self.sessions.pop(h, None)
            self.refresh_contacts()

    def on_resize(self, event) -> None:
        if hasattr(self, "active_peer_hash") and self.active_peer_hash:
            log = self.query_one("#chat-log", RichLog)
            log.clear()
            for m in self.chat_buffers.get(self.active_peer_hash, []):
                self.write_message_to_log(m["sender"], m["text"], m["ts"], self.active_peer_hash)

    def refresh_contacts(self) -> None:
        if not self.is_mounted or self._closing or getattr(self, "_pruning", False):
            return

        try:
            lv = self.query_one("#contacts-list", ListView)
        except Exception:
            return

        if not lv.is_mounted or not lv.is_attached:
            return

        lv.clear()
        items = []
        seen_hashes = set()
        for alias, data in self.storage.list_contacts().items():
            if isinstance(data, dict):
                h = clean_hash(data.get("onion", ""))
                name = data.get("nickname") or alias
            else:
                h = clean_hash(data)
                name = alias

            if not h or h == self.local_onion_hash or h in seen_hashes:
                continue
            seen_hashes.add(h)

            cls = "online" if h in self.sessions else "offline"
            status = "●" if cls == "online" else "○"
            unread_cnt = self.unread_counts.get(h, 0)
            unread = f" [{unread_cnt}]" if unread_cnt > 0 else ""
            label = f"[{cls}]{status}[/] {name}{unread}"
            items.append(ListItem(Label(label), name=h))

        if items:
            lv.extend(items)

    def on_list_view_selected(self, event: ListView.Selected):
        h = event.item.name
        alias = self.storage.find_alias_by_onion(h) or f"peer-{h[:6]}"
        self.active_peer_hash = h
        self.unread_counts[h] = 0
        
        status_text = "[E2EE Secured]" if h in self.sessions else "(Offline)"
        self.query_one("#chat-header", Static).update(f"Chat: {alias} {status_text}")
        
        log = self.query_one("#chat-log", RichLog)
        log.clear()
        for m in self.chat_buffers.get(h, []):
            self.write_message_to_log(m["sender"], m["text"], m["ts"], h)
            
        if h not in self.sessions:
            self.run_worker(self._connect_to_peer(h, alias))
            
        self.refresh_contacts()

    async def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        h = self.active_peer_hash
        if not text or not h or h not in self.sessions: return
        event.input.value = ""
        ts = time.strftime("%H:%M")
        self.logger.info(f"Outgoing message sent to peer {h}")
        await self.sessions[h].send_op(OP_CHAT, {"m": text, "ts": ts})
        msg = {"sender": "me", "text": text, "ts": ts}
        if h not in self.chat_buffers: self.chat_buffers[h] = []
        self.chat_buffers[h].append(msg)
        self.write_message_to_log("me", text, ts, h)

    async def on_unmount(self):
        self._closing = True
        
        # Cancel all workers (including tor-init)
        for worker in self.workers:
            worker.cancel()
            
        for s in list(self.sessions.values()):
            try: await s.close()
            except Exception: pass
        self.sessions.clear()
        
        if hasattr(self, 'server') and self.server:
            try:
                await self.server.stop()
            except Exception: pass
            
        if hasattr(self, 'controller') and self.controller:
            try:
                await asyncio.to_thread(self.controller.close)
            except Exception: pass

    async def action_quit(self):
        self.exit()


