import pytest

from auditize.config import Config, get_config
from auditize.exceptions import ConfigError

MINIMUM_VIABLE_CONFIG = {"AUDITIZE_JWT_SIGNING_KEY": "DUMMYKEY"}


def test_get_config():
    # test get_config assuming environment variables set in conftest.py
    config = get_config()
    assert isinstance(config, Config)
    assert config.base_url == "http://localhost:8000"
    assert config.jwt_signing_key is not None
    assert config.user_session_token_lifetime == 43200  # 12 hours
    assert config.attachment_max_size == 1024
    assert config.mongodb_uri is None
    assert config.smtp_server is None
    assert config.smtp_port is None
    assert config.smtp_username is None
    assert config.smtp_password is None
    assert config.smtp_sender is None
    assert config.is_smtp_enabled() is False
    assert config.cors_allow_origins == []
    assert config.cors_allow_credentials is False
    assert config.cors_allow_methods == []
    assert config.cors_allow_headers == []
    assert config.is_cors_enabled() is False


def test_config_without_mandatory_variable():
    for key in MINIMUM_VIABLE_CONFIG:
        with pytest.raises(ConfigError):
            Config.load_from_env(
                {k: v for k, v in MINIMUM_VIABLE_CONFIG.items() if k != key}
            )


def test_config_minimum_viable_config():
    config = Config.load_from_env(MINIMUM_VIABLE_CONFIG)
    assert config.base_url == "http://localhost:8000"
    assert config.jwt_signing_key == MINIMUM_VIABLE_CONFIG["AUDITIZE_JWT_SIGNING_KEY"]
    assert config.user_session_token_lifetime == 43200  # 12 hours
    assert config.attachment_max_size == 5242880  # 5MB
    assert config.mongodb_uri is None
    assert config.smtp_server is None
    assert config.smtp_port is None
    assert config.smtp_username is None
    assert config.smtp_password is None
    assert config.smtp_sender is None
    assert config.is_smtp_enabled() is False
    assert config.cors_allow_credentials is False
    assert config.cors_allow_methods == []
    assert config.cors_allow_headers == []
    assert config.is_cors_enabled() is False


def test_config_var_mongodb_uri():
    config = Config.load_from_env(
        {**MINIMUM_VIABLE_CONFIG, "AUDITIZE_MONGODB_URI": "mongodb://localhost:27017"}
    )
    assert config.mongodb_uri == "mongodb://localhost:27017"


def test_config_var_user_session_token_lifetime():
    config = Config.load_from_env(
        {**MINIMUM_VIABLE_CONFIG, "AUDITIZE_USER_SESSION_TOKEN_LIFETIME": "3600"}
    )
    assert config.user_session_token_lifetime == 3600


def test_config_var_attachment_max_size():
    config = Config.load_from_env(
        {**MINIMUM_VIABLE_CONFIG, "AUDITIZE_ATTACHMENT_MAX_SIZE": "1048576"}
    )
    assert config.attachment_max_size == 1048576


def test_config_smtp_enabled():
    config = Config.load_from_env(
        {
            **MINIMUM_VIABLE_CONFIG,
            "AUDITIZE_SMTP_SERVER": "smtp.example.com",
            "AUDITIZE_SMTP_PORT": "587",
            "AUDITIZE_SMTP_USERNAME": "user",
            "AUDITIZE_SMTP_PASSWORD": "password",
        }
    )
    assert config.is_smtp_enabled() is True
    assert config.smtp_server == "smtp.example.com"
    assert config.smtp_port == 587
    assert config.smtp_username == "user"
    assert config.smtp_password == "password"
    assert config.smtp_sender == "user"


def test_config_smtp_enabled_custom_sender():
    config = Config.load_from_env(
        {
            **MINIMUM_VIABLE_CONFIG,
            "AUDITIZE_SMTP_SERVER": "smtp.example.com",
            "AUDITIZE_SMTP_PORT": "587",
            "AUDITIZE_SMTP_USERNAME": "user",
            "AUDITIZE_SMTP_PASSWORD": "password",
            "AUDITIZE_SMTP_SENDER": "custom_sender",
        }
    )
    assert config.is_smtp_enabled() is True
    assert config.smtp_server == "smtp.example.com"
    assert config.smtp_port == 587
    assert config.smtp_username == "user"
    assert config.smtp_password == "password"
    assert config.smtp_sender == "custom_sender"


def test_config_smtp_invalid():
    with pytest.raises(ConfigError, match="SMTP configuration is incomplete"):
        Config.load_from_env(
            {
                **MINIMUM_VIABLE_CONFIG,
                "AUDITIZE_SMTP_SERVER": "smtp.example.com",
                "AUDITIZE_SMTP_PORT": "587",
                "AUDITIZE_SMTP_USERNAME": "user",
                # missing password
            }
        )


def test_config_cors_enabled():
    config = Config.load_from_env(
        {
            **MINIMUM_VIABLE_CONFIG,
            "AUDITIZE_CORS_ALLOW_ORIGINS": "http://localhost:5173",
            "AUDITIZE_CORS_ALLOW_CREDENTIALS": "true",
            "AUDITIZE_CORS_ALLOW_METHODS": "GET,POST,PATCH,DELETE",
            "AUDITIZE_CORS_ALLOW_HEADERS": "*",
        }
    )
    assert config.is_cors_enabled() is True
    assert config.cors_allow_origins == ["http://localhost:5173"]
    assert config.cors_allow_credentials is True
    assert config.cors_allow_methods == ["GET", "POST", "PATCH", "DELETE"]
    assert config.cors_allow_headers == ["*"]


def test_config_cors_enabled_bis():
    config = Config.load_from_env(
        {
            **MINIMUM_VIABLE_CONFIG,
            "AUDITIZE_CORS_ALLOW_ORIGINS": "http://localhost:5173",
            "AUDITIZE_CORS_ALLOW_CREDENTIALS": "false",
            "AUDITIZE_CORS_ALLOW_METHODS": "*",
        }
    )
    assert config.is_cors_enabled() is True
    assert config.cors_allow_origins == ["http://localhost:5173"]
    assert config.cors_allow_credentials is False
    assert config.cors_allow_methods == ["*"]
    assert config.cors_allow_headers == []
