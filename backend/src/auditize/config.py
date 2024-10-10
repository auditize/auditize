import dataclasses
import os

from apscheduler.triggers.cron import CronTrigger
from dotenv import dotenv_values

from auditize.exceptions import (
    ConfigAlreadyInitialized,
    ConfigError,
    ConfigNotInitialized,
)

_DEFAULT_ATTACHMENT_MAX_SIZE = 1024 * 1024 * 5  # 5MB
_DEFAULT_CSV_MAX_ROWS = 10_000
_DEFAULT_USER_SESSION_TOKEN_LIFETIME = 60 * 60 * 12  # 12 hours
_DEFAULT_ACCESS_TOKEN_LIFETIME = 10 * 60  # 10 minutes
_DEFAULT_LOG_EXPIRATION_SCHEDULE = "0 1 * * *"


@dataclasses.dataclass
class Config:
    public_url: str
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
    cookie_secure: bool
    test_mode: bool
    online_doc: bool
    log_expiration_schedule: str

    @staticmethod
    def _validate_list(value):
        return value.split(",")

    @staticmethod
    def _validate_bool(value):
        if value == "true":
            return True
        if value == "false":
            return False
        raise ValueError(f"must be either 'true' or 'false'")

    @staticmethod
    def _validate_cron_expr(value):
        try:
            CronTrigger.from_crontab(value)
        except ValueError as exc:
            raise ValueError(f"not a valid cron expression ({exc})")
        return value

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
    def _load_from_env(cls, env):
        def required(key, validator=None):
            value = env[key]
            if validator:
                try:
                    value = validator(value)
                except ValueError as exc:
                    raise ConfigError(
                        f"Could not load configuration, invalid value {value!r} for {key!r}: {exc}"
                    )
            return value

        def optional(key, default=None, validator=None):
            try:
                return required(key, validator)
            except KeyError:
                return default

        try:
            config = cls(
                public_url=required("AUDITIZE_PUBLIC_URL"),
                jwt_signing_key=required("AUDITIZE_JWT_SIGNING_KEY"),
                user_session_token_lifetime=optional(
                    "AUDITIZE_USER_SESSION_TOKEN_LIFETIME",
                    _DEFAULT_USER_SESSION_TOKEN_LIFETIME,
                    validator=int,
                ),
                access_token_lifetime=optional(
                    "AUDITIZE_ACCESS_TOKEN_LIFETIME",
                    _DEFAULT_ACCESS_TOKEN_LIFETIME,
                    validator=int,
                ),
                attachment_max_size=optional(
                    "AUDITIZE_ATTACHMENT_MAX_SIZE",
                    default=_DEFAULT_ATTACHMENT_MAX_SIZE,
                    validator=int,
                ),
                csv_max_rows=optional(
                    "AUDITIZE_CSV_MAX_ROWS",
                    default=_DEFAULT_CSV_MAX_ROWS,
                    validator=int,
                ),
                mongodb_uri=optional("AUDITIZE_MONGODB_URI"),
                smtp_server=optional("AUDITIZE_SMTP_SERVER"),
                smtp_port=optional("AUDITIZE_SMTP_PORT", validator=int),
                smtp_username=optional("AUDITIZE_SMTP_USERNAME"),
                smtp_password=optional("AUDITIZE_SMTP_PASSWORD"),
                _smtp_sender=optional("AUDITIZE_SMTP_SENDER"),
                cors_allow_origins=optional(
                    "AUDITIZE_CORS_ALLOW_ORIGINS",
                    validator=cls._validate_list,
                    default=[],
                ),
                log_expiration_schedule=optional(
                    "AUDITIZE_LOG_EXPIRATION_SCHEDULE",
                    validator=cls._validate_cron_expr,
                    default=_DEFAULT_LOG_EXPIRATION_SCHEDULE,
                ),
                cookie_secure=optional(
                    "AUDITIZE_COOKIE_SECURE",
                    validator=cls._validate_bool,
                    default=False,
                ),
                ###
                # "Private" configuration
                ###
                test_mode=optional(
                    "_AUDITIZE_TEST_MODE", validator=cls._validate_bool, default=False
                ),
                online_doc=optional(
                    "_AUDITIZE_ONLINE_DOC", validator=cls._validate_bool, default=False
                ),
            )
        except KeyError as e:
            var_name = str(e)
            raise ConfigError(
                f"Could not load configuration, variable {var_name} is missing"
            )

        config._validate()

        return config

    @classmethod
    def load_from_env(cls, env=None):
        if env is None:
            env = os.environ

        if "AUDITIZE_CONFIG" in env:
            try:
                with open(env["AUDITIZE_CONFIG"]) as fh:
                    env = dotenv_values(stream=fh)
            except IOError as exc:
                raise ConfigError(
                    f"Could not load configuration from {env['AUDITIZE_CONFIG']!r}: {exc}"
                )

        return cls._load_from_env(env)

    @property
    def smtp_sender(self):
        return self._smtp_sender or self.smtp_username

    def is_smtp_enabled(self):
        return self.smtp_sender is not None

    def to_dict(self):
        return dataclasses.asdict(self)


_config: Config | None = None


def init_config(env=None) -> Config:
    global _config
    if _config:
        raise ConfigAlreadyInitialized()
    _config = Config.load_from_env(env)
    return _config


def get_config() -> Config:
    if not _config:
        raise ConfigNotInitialized()
    return _config
