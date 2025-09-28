import os

import pytest

from auditize.config import Config, get_config
from auditize.exceptions import ConfigError

MINIMUM_VIABLE_CONFIG = {
    "AUDITIZE_PUBLIC_URL": "http://localhost:8000",
    "AUDITIZE_JWT_SIGNING_KEY": "DUMMYKEY",
}


def test_get_config():
    # test get_config assuming environment variables set in conftest.py
    config = get_config()
    assert isinstance(config, Config)
    assert config.public_url == "http://localhost:8000"
    assert config.jwt_signing_key is not None
    assert config.postgres_host == "localhost"
    assert config.postgres_port == 5432
    assert config.postgres_user is not None
    assert config.postgres_password is not None
    assert config.elastic_url == "https://localhost:9200"
    assert config.elastic_user == "elastic"
    assert config.elastic_password
    assert config.elastic_ssl_verify is False
    assert config.user_session_token_lifetime == 43200  # 12 hours
    assert config.access_token_lifetime == 600  # 10 minutes
    assert config.attachment_max_size == 1024
    assert config.csv_max_rows == 10
    # NB: don't check the actual value, since it can be changed
    # when pytest-xdist is used
    assert config.db_name
    assert config.smtp_server is None
    assert config.smtp_port is None
    assert config.smtp_username is None
    assert config.smtp_password is None
    assert config.smtp_sender is None
    assert config.is_smtp_enabled() is False
    assert config.cors_allow_origins == []
    assert config.log_expiration_schedule == "0 1 * * *"
    assert config.cookie_secure is False
    assert config.test_mode is True
    assert config.online_doc is False


def test_config_without_mandatory_variable():
    for key in MINIMUM_VIABLE_CONFIG:
        with pytest.raises(ConfigError):
            Config.load_from_env(
                {k: v for k, v in MINIMUM_VIABLE_CONFIG.items() if k != key}
            )


def test_config_minimum_viable_config():
    config = Config.load_from_env(MINIMUM_VIABLE_CONFIG)
    assert config.public_url == "http://localhost:8000"
    assert config.jwt_signing_key == MINIMUM_VIABLE_CONFIG["AUDITIZE_JWT_SIGNING_KEY"]
    assert config.elastic_url == "http://localhost:9200"
    assert config.elastic_user is None
    assert config.elastic_password is None
    assert config.elastic_ssl_verify is True
    assert config.postgres_host == "localhost"
    assert config.postgres_port == 5432
    assert not config.postgres_password
    assert config.user_session_token_lifetime == 43200  # 12 hours
    assert config.access_token_lifetime == 600  # 10 minutes
    assert config.attachment_max_size == 5242880  # 5MB
    assert config.csv_max_rows == 10_000
    assert config.db_name == "auditize"
    assert config.smtp_server is None
    assert config.smtp_port is None
    assert config.smtp_username is None
    assert config.smtp_password is None
    assert config.smtp_sender is None
    assert config.is_smtp_enabled() is False
    assert config.cors_allow_origins == []
    assert config.log_expiration_schedule == "0 1 * * *"
    assert config.cookie_secure is False
    assert config.test_mode is False
    assert config.online_doc is False


def test_config_var_db_name():
    config = Config.load_from_env(
        {**MINIMUM_VIABLE_CONFIG, "AUDITIZE_DB_NAME": "my_db"}
    )
    assert config.db_name == "my_db"


def test_config_custom_postgres():
    config = Config.load_from_env(
        {
            **MINIMUM_VIABLE_CONFIG,
            "AUDITIZE_PG_HOST": "db.example.com",
            "AUDITIZE_PG_PORT": "6543",
            "AUDITIZE_PG_USER": "myuser",
            "AUDITIZE_PG_PASSWORD": "mypassword",
        }
    )
    assert config.postgres_host == "db.example.com"
    assert config.postgres_port == 6543
    assert config.postgres_user == "myuser"
    assert config.postgres_password == "mypassword"


def test_config_elastic_disable_ssl_verify():
    config = Config.load_from_env(
        {**MINIMUM_VIABLE_CONFIG, "AUDITIZE_ES_SSL_VERIFY": "false"}
    )
    assert config.elastic_ssl_verify is False


def test_config_elastic_user_and_password_incomplete():
    with pytest.raises(ConfigError, match="incomplete"):
        Config.load_from_env({**MINIMUM_VIABLE_CONFIG, "AUDITIZE_ES_USER": "elastic"})


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


def test_config_var_log_expiration_schedule():
    config = Config.load_from_env(
        {**MINIMUM_VIABLE_CONFIG, "AUDITIZE_LOG_EXPIRATION_SCHEDULE": "0 0 * * *"}
    )
    assert config.log_expiration_schedule == "0 0 * * *"


def test_config_var_log_expiration_schedule_invalid():
    with pytest.raises(ConfigError):
        Config.load_from_env(
            {
                **MINIMUM_VIABLE_CONFIG,
                "AUDITIZE_LOG_EXPIRATION_SCHEDULE": "not a valid cron expression",
            }
        )


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
        }
    )
    assert config.cors_allow_origins == ["http://localhost:5173"]


def test_config_cookie_secure_turned_on():
    config = Config.load_from_env(
        {**MINIMUM_VIABLE_CONFIG, "AUDITIZE_COOKIE_SECURE": "true"}
    )
    assert config.cookie_secure is True


def test_config_from_file(tmp_path):
    env_file = tmp_path / "env"
    with env_file.open("w") as fh:
        fh.write(
            """
            AUDITIZE_PUBLIC_URL=http://localhost:8000
            AUDITIZE_JWT_SIGNING_KEY=SECRET
            AUDITIZE_ES_URL=http://localhost:9200
            AUDITIZE_ES_USER=elastic
            AUDITIZE_ES_PASSWORD=password
            AUDITIZE_PG_USER=postgres
            AUDITIZE_PG_PASSWORD=password
            """
        )
    config = Config.load_from_env(
        {
            "AUDITIZE_CONFIG": str(env_file),
            "AUDITIZE_CORS_ALLOW_ORIGINS": "http://localhost:5173",
        }
    )
    assert config.public_url == "http://localhost:8000"
    assert config.jwt_signing_key == "SECRET"
    assert (
        config.cors_allow_origins == []
    )  # make sure that AUDITIZE_CONFIG content has precedence over env variables


def test_config_from_unknown_file():
    with pytest.raises(ConfigError, match="/this/file/does/not/exist"):
        Config.load_from_env({"AUDITIZE_CONFIG": "/this/file/does/not/exist"})
