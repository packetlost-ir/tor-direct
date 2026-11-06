import asyncio
import traceback
import logging
from tortalk.network.protocol import perform_protocol_handshake

logger = logging.getLogger("tork.network.server")

class PeerServer:
    def __init__(self, host, port, local_hash, local_name, session_callback):
        self.host = host
        self.port = port
        self.local_hash = local_hash
        self.local_name = local_name
        self.session_callback = session_callback
        self.server = None

    async def _handle_connection(self, reader, writer):
        peer_addr = writer.get_extra_info('peername')
        logger.info(f"Incoming connection accepted from {peer_addr}")
        try:
            shared_key, peer_hash, peer_name = await perform_protocol_handshake(
                reader, writer, self.local_hash, self.local_name, False
            )
            logger.info(f"Handshake successful with peer {peer_hash} ({peer_name})")
            await self.session_callback(reader, writer, shared_key, peer_hash, peer_name, False)
        except Exception as e:
            logger.error(f"Error handling connection from {peer_addr}: {e}", exc_info=True)
            writer.close()
            try: await writer.wait_closed()
            except Exception: pass

    async def start(self):
        logger.info(f"Starting PeerServer on {self.host}:{self.port}")
        self.server = await asyncio.start_server(self._handle_connection, self.host, self.port)
        logger.info("PeerServer listening successfully")

    async def stop(self):
        if self.server:
            logger.info("Stopping PeerServer")
            self.server.close()
            await self.server.wait_closed()
            logger.info("PeerServer stopped")
