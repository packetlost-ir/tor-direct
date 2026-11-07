from stem.control import Controller
from t0rd.config import CONTROL_PORT
import time

def get_controller(control_port: int = CONTROL_PORT, password: str | None = None) -> Controller:
    try:
        controller = Controller.from_port(port=control_port)
    except Exception as e:
        raise ConnectionError(f"Could not connect to Tor control port {control_port}: {e}")
        
    try:
        controller.authenticate(password=password)
    except Exception as e:
        controller.close()
        raise PermissionError(f"Tor authentication failed: {e}")
        
    return controller

def wait_for_bootstrap(controller: Controller, timeout: int = 60) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            bootstrap = controller.get_info("status/bootstrap-phase")
            if "PROGRESS=100" in bootstrap:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def create_onion_service(
    controller: Controller,
    local_port: int,
    key_type: str = "NEW",
    key_content: str = "ED25519-V3",
    await_publication: bool = True
) -> tuple[str, str, str]:
    # Ensure Tor is bootstrapped before creating service if we wait for publication
    if await_publication and not wait_for_bootstrap(controller, timeout=30):
        # We still try, but publication might take longer
        pass
        
    response = controller.create_ephemeral_hidden_service(
        {80: local_port},
        await_publication=await_publication,
        key_type=key_type,
        key_content=key_content,
        discard_key=False
    )
    service_id = response.service_id
    if service_id.endswith(".onion"):
        service_id = service_id[:-6]
    return service_id, response.private_key_type, response.private_key

def destroy_onion_service(controller: Controller, onion_address: str) -> None:
    service_id = onion_address
    if service_id.endswith(".onion"):
        service_id = service_id[:-6]
    try:
        controller.remove_ephemeral_hidden_service(service_id)
    except Exception:
        pass
