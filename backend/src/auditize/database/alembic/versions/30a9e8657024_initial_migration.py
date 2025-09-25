"""Initial migration

Revision ID: 30a9e8657024
Revises:
Create Date: 2025-09-14 17:36:39.653074

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "30a9e8657024"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "log_i18n_profile",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_log_i18n_profile")),
    )
    op.create_index(
        op.f("ix_log_i18n_profile_name"), "log_i18n_profile", ["name"], unique=True
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("is_superadmin", sa.Boolean(), nullable=False),
        sa.Column("repos_read", sa.Boolean(), nullable=False),
        sa.Column("repos_write", sa.Boolean(), nullable=False),
        sa.Column("users_read", sa.Boolean(), nullable=False),
        sa.Column("users_write", sa.Boolean(), nullable=False),
        sa.Column("apikeys_read", sa.Boolean(), nullable=False),
        sa.Column("apikeys_write", sa.Boolean(), nullable=False),
        sa.Column("logs_read", sa.Boolean(), nullable=False),
        sa.Column("logs_write", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions")),
    )
    op.create_table(
        "apikey",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=True),
        sa.Column("permissions_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permissions_id"],
            ["permissions.id"],
            name=op.f("fk_apikey_permissions_id"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_apikey")),
    )
    op.create_index(op.f("ix_apikey_name"), "apikey", ["name"], unique=True)
    op.create_table(
        "log_i18n_profile_translation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lang", sa.String(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("labels", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"],
            ["log_i18n_profile.id"],
            name=op.f("fk_log_i18n_profile_translation_profile_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_log_i18n_profile_translation")),
    )
    op.create_table(
        "repo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("log_db_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("retention_period", sa.Integer(), nullable=True),
        sa.Column("log_i18n_profile_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["log_i18n_profile_id"],
            ["log_i18n_profile.id"],
            name=op.f("fk_repo_log_i18n_profile_id"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_repo")),
        sa.UniqueConstraint("log_db_name", name=op.f("uq_repo_log_db_name")),
    )
    op.create_index(op.f("ix_repo_name"), "repo", ["name"], unique=True)
    op.create_table(
        "user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("lang", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("password_reset_token", sa.String(), nullable=True),
        sa.Column(
            "password_reset_token_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("authenticated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("permissions_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permissions_id"], ["permissions.id"], name=op.f("fk_user_permissions_id")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user")),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_index(op.f("ix_user_first_name"), "user", ["first_name"], unique=False)
    op.create_index(op.f("ix_user_last_name"), "user", ["last_name"], unique=False)
    op.create_table(
        "log_entity",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repo_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("ref", sa.String(), nullable=False),
        sa.Column("parent_entity_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_entity_id"],
            ["log_entity.id"],
            name=op.f("fk_log_entity_parent_entity_id"),
        ),
        sa.ForeignKeyConstraint(
            ["repo_id"],
            ["repo.id"],
            name=op.f("fk_log_entity_repo_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_log_entity")),
        sa.UniqueConstraint("repo_id", "ref", name=op.f("uq_log_entity_repo_id")),
    )
    op.create_table(
        "log_filter",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("repo_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "search_params",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "columns",
            sa.String(),
            nullable=False,
        ),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["repo_id"],
            ["repo.id"],
            name=op.f("fk_log_filter_repo_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_log_filter_user_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_log_filter")),
    )
    op.create_index(op.f("ix_log_filter_name"), "log_filter", ["name"], unique=True)
    op.create_table(
        "permissions_repo_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repo_id", sa.Uuid(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("write", sa.Boolean(), nullable=False),
        sa.Column("permissions_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permissions_id"],
            ["permissions.id"],
            name=op.f("fk_permissions_repo_log_permissions_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["repo_id"],
            ["repo.id"],
            name=op.f("fk_permissions_repo_log_repo_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions_repo_log")),
    )
    op.create_table(
        "permissions_readable_log_entity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ref", sa.String(), nullable=False),
        sa.Column("repo_log_permissions_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["repo_log_permissions_id"],
            ["permissions_repo_log.id"],
            name=op.f("fk_permissions_readable_log_entity_repo_log_permissions_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions_readable_log_entity")),
    )


def downgrade() -> None:
    op.drop_table("permissions_readable_log_entity")
    op.drop_table("permissions_repo_log")
    op.drop_index(op.f("ix_log_filter_name"), table_name="log_filter")
    op.drop_table("log_filter")
    op.drop_table("log_entity")
    op.drop_index(op.f("ix_user_last_name"), table_name="user")
    op.drop_index(op.f("ix_user_first_name"), table_name="user")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_repo_name"), table_name="repo")
    op.drop_table("repo")
    op.drop_table("log_i18n_profile_translation")
    op.drop_index(op.f("ix_apikey_name"), table_name="apikey")
    op.drop_table("apikey")
    op.drop_table("permissions")
    op.drop_index(op.f("ix_log_i18n_profile_name"), table_name="log_i18n_profile")
    op.drop_table("log_i18n_profile")
