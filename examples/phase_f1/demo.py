from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_gateway import AIGateway, GatewayRequest
from ai_gateway.audit import JsonlAuditSink
from ai_gateway.config import load_gateway_configuration


def main() -> None:
    config = PROJECT_ROOT / "examples" / "phase_f1" / "gateway.json"
    routes, retry, options = load_gateway_configuration(config)
    gateway = AIGateway(
        routes=routes,
        retry_policy=retry,
        requests_per_second=float(options["requests_per_second"]),
        audit_sink=JsonlAuditSink(PROJECT_ROOT / str(options["audit_path"])),
    )
    response = gateway.invoke(
        GatewayRequest(
            route="manual-demo",
            prompt="Predict the next prime gap.",
            json_mode=True,
            metadata={"case_id": "F1-DEMO"},
        )
    )
    print(response.to_dict())


if __name__ == "__main__":
    main()
