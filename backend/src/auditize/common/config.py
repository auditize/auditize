import dataclasses
import os
from threading import Lock


@dataclasses.dataclass
class Config:
    base_url: str
    user_session_token_signing_key: str
    user_session_token_lifetime: int
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    _smtp_sender: str

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
            return cls(
                base_url=optional("AUDITIZE_BASE_URL", "http://localhost:8000"),
                user_session_token_signing_key=required(
                    "AUDITIZE_USER_SESSION_TOKEN_SIGNING_KEY"
                ),
                user_session_token_lifetime=optional(
                    "AUDITIZE_USER_SESSION_TOKEN_LIFETIME", 60 * 60 * 12, cast=int
                ),
                smtp_server=optional("AUDITIZE_SMTP_SERVER"),
                smtp_port=optional("AUDITIZE_SMTP_PORT", cast=int),
                smtp_username=optional("AUDITIZE_SMTP_USERNAME"),
                smtp_password=optional("AUDITIZE_SMTP_PASSWORD"),
                _smtp_sender=optional("AUDITIZE_SMTP_SENDER"),
            )
        except KeyError as e:
            var_name = str(e)
            raise ValueError(
                f"Could not load configuration, variable {var_name} is missing"
            )

    @property
    def smtp_sender(self):
        return self._smtp_sender or self.smtp_username

    def is_smtp_enabled(self):
        return all(
            (self.smtp_server, self.smtp_port, self.smtp_username, self.smtp_password)
        )


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
