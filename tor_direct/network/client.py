import asyncio
import logging
from python_socks import ProxyType, ProxyError
from python_socks.async_.asyncio import Proxy
from tor_direct.config import normalize_and_validate_onion, SOCKS_HOST, SOCKS_PORT, CONNECT_TIMEOUT

logger = logging.getLogger("tor_direct.network.client")

async def connect_peer(target_onion, socks_host=SOCKS_HOST, socks_port=SOCKS_PORT, timeout=CONNECT_TIMEOUT):
    is_valid, normalized_addr, err = normalize_and_validate_onion(target_onion)
    if not is_valid:
        logger.error(f"Invalid peer address: {err}")
        raise ValueError(f"Invalid address: {err}")
    
    logger.info(f"Connecting to peer {normalized_addr} via SOCKS5 {socks_host}:{socks_port} (timeout={timeout}s)")
    proxy = Proxy.create(proxy_type=ProxyType.SOCKS5, host=socks_host, port=socks_port, rdns=True)
    
    for attempt in range(6):
        try:
            sock = await asyncio.wait_for(proxy.connect(dest_host=normalized_addr, dest_port=80), timeout=timeout)
            logger.info(f"Successfully connected to peer {normalized_addr}")
            return await asyncio.open_connection(sock=sock)
        except (ProxyError, OSError, asyncio.TimeoutError) as e:
            logger.warning(f"Connection attempt {attempt + 1}/6 failed to {normalized_addr}: {e}")
            if attempt == 5:
                logger.error(f"All connection attempts failed to {normalized_addr}")
                raise ConnectionError(f"Target unreachable: {e}")
            await asyncio.sleep(min(15, timeout / 2))
