import dataclasses
import json
import os
from threading import Lock

from auditize.exceptions import ConfigError

_DEFAULT_ATTACHMENT_MAX_SIZE = 1024 * 1024 * 5  # 5MB
_DEFAULT_CSV_MAX_ROWS = 10_000


@dataclasses.dataclass
class Config:
    base_url: str
    jwt_signing_key: str
    user_session_token_lifetime: int
    access_token_lifetime: int
    attachment_max_size: int
    csv_max_rows: int
    mongodb_uri: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    _smtp_sender: str
    cors_allow_origins: list[str]
    cors_allow_credentials: bool
    cors_allow_methods: list[str]
    cors_allow_headers: list[str]

    @staticmethod
    def _cast_list(value):
        return value.split(",")

    @staticmethod
    def _cast_bool(value):
        return value.lower() in ("true", "yes", "1")

    def _validate(self):
        smtp_values_required = (
            self.smtp_server,
            self.smtp_port,
            self.smtp_username,
            self.smtp_password,
        )
        smtp_values = smtp_values_required + (self._smtp_sender,)

        if any(smtp_values) and not all(smtp_values_required):
            raise ConfigError(
                "SMTP configuration is incomplete, please provide all of the following environment variables:\n"
                "- AUDITIZE_SMTP_SERVER\n"
                "- AUDITIZE_SMTP_PORT\n"
                "- AUDITIZE_SMTP_USERNAME\n"
                "- AUDITIZE_SMTP_PASSWORD\n"
            )

    @classmethod
    def load_from_env(cls, env=None):
        if env is None:
            env = os.environ

        def required(key, cast=None):
            value = env[key]
            if cast:
                value = cast(value)
            return value

        def optional(key, default=None, cast=None):
            try:
                return required(key, cast)
            except KeyError:
                return default

        try:
            config = cls(
                base_url=optional("AUDITIZE_BASE_URL", "http://localhost:8000"),
                jwt_signing_key=required("AUDITIZE_JWT_SIGNING_KEY"),
                user_session_token_lifetime=optional(
                    "AUDITIZE_USER_SESSION_TOKEN_LIFETIME", 60 * 60 * 12, cast=int
                ),
                access_token_lifetime=optional(
                    "AUDITIZE_ACCESS_TOKEN_LIFETIME", 60 * 60, cast=int
                ),
                attachment_max_size=optional(
                    "AUDITIZE_ATTACHMENT_MAX_SIZE",
                    default=_DEFAULT_ATTACHMENT_MAX_SIZE,
                    cast=int,
                ),
                csv_max_rows=optional(
                    "AUDITIZE_CSV_MAX_ROWS", default=_DEFAULT_CSV_MAX_ROWS, cast=int
                ),
                mongodb_uri=optional("AUDITIZE_MONGODB_URI"),
                smtp_server=optional("AUDITIZE_SMTP_SERVER"),
                smtp_port=optional("AUDITIZE_SMTP_PORT", cast=int),
                smtp_username=optional("AUDITIZE_SMTP_USERNAME"),
                smtp_password=optional("AUDITIZE_SMTP_PASSWORD"),
                _smtp_sender=optional("AUDITIZE_SMTP_SENDER"),
                cors_allow_origins=optional(
                    "AUDITIZE_CORS_ALLOW_ORIGINS", cast=cls._cast_list, default=[]
                ),
                cors_allow_credentials=optional(
                    "AUDITIZE_CORS_ALLOW_CREDENTIALS",
                    cast=cls._cast_bool,
                    default=False,
                ),
                cors_allow_methods=optional(
                    "AUDITIZE_CORS_ALLOW_METHODS",
                    cast=cls._cast_list,
                    default=[],
                ),
                cors_allow_headers=optional(
                    "AUDITIZE_CORS_ALLOW_HEADERS",
                    cast=cls._cast_list,
                    default=[],
                ),
            )
        except KeyError as e:
            var_name = str(e)
            raise ConfigError(
                f"Could not load configuration, variable {var_name} is missing"
            )

        config._validate()

        return config

    @property
    def smtp_sender(self):
        return self._smtp_sender or self.smtp_username

    def is_smtp_enabled(self):
        return self.smtp_sender is not None

    def is_cors_enabled(self):
        return bool(self.cors_allow_origins)


_config = None
_config_lock = Lock()


def get_config() -> Config:
    global _config
    # we make an initial check outside of lock to avoid unneeded locking when config is already loaded
    if _config is None:
        with _config_lock:
            if _config is None:
                _config = Config.load_from_env()
    return _config


def _print_config():
    config = Config.load_from_env()
    print(json.dumps(dataclasses.asdict(config), ensure_ascii=False, indent=4))


# Print the actual auditize configuration with "python -m auditize.config"
if __name__ == "__main__":
    _print_config()
