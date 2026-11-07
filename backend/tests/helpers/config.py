import os
from pathlib import Path

from dotenv import dotenv_values

# Source env from this file if its exists.
_ENV_TEST_FILE = Path(__file__).parent.parent.parent / ".env.test"


def get_test_config_vars() -> dict[str, str]:
    # environment variables take precedence over the .env.test file
    env = {**dotenv_values(_ENV_TEST_FILE), **os.environ}
    return {
        "AUDITIZE_ES_URL": env.get("ES_URL", "https://localhost:9200"),
        "AUDITIZE_ES_USER": env.get("ES_USER", "elastic"),
        "AUDITIZE_ES_PASSWORD": env["ES_PASSWORD"],
        "AUDITIZE_ES_SSL_VERIFY": "false",
        "AUDITIZE_PG_HOST": env.get("PG_HOST", "localhost"),
        "AUDITIZE_PG_PORT": env.get("PG_PORT", "5432"),
        "AUDITIZE_PG_USER": env.get("PG_USER", env.get("USER", "")),
        "AUDITIZE_PG_PASSWORD": env.get("PG_PASSWORD", ""),
        "AUDITIZE_PUBLIC_URL": "http://localhost:8000",
        "AUDITIZE_JWT_SIGNING_KEY": "917c5d359493bf90140e4f725b351d2282a6c23bb78d096cb7913d7090375a73",
        "AUDITIZE_ATTACHMENT_MAX_SIZE": "1024",
        "AUDITIZE_EXPORT_MAX_ROWS": "10",
        "_AUDITIZE_TEST_MODE": "true",
    }
