"""add tipo, iscrizione_id, trasferimento_id to flussi_cassa

Revision ID: 5b0fd2895d05
Revises: 9c36141f6eed
Create Date: 2026-06-20 23:16:53.183872

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5b0fd2895d05"
down_revision: str | Sequence[str] | None = "8b23e062dcd8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

tipo_flusso_cassa = postgresql.ENUM(
    "MOVIMENTO",
    "SALDO_INIZIALE",
    "TRASFERIMENTO_USCITA",
    "TRASFERIMENTO_ENTRATA",
    "AUTO_ISCRIZIONE",
    name="tipo_flusso_cassa",
)


def upgrade() -> None:
    tipo_flusso_cassa.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "flussi_cassa",
        sa.Column(
            "tipo",
            sa.Enum(
                "MOVIMENTO",
                "SALDO_INIZIALE",
                "TRASFERIMENTO_USCITA",
                "TRASFERIMENTO_ENTRATA",
                "AUTO_ISCRIZIONE",
                name="tipo_flusso_cassa",
                create_type=False,
            ),
            nullable=False,
            server_default="MOVIMENTO",
        ),
    )
    op.add_column(
        "flussi_cassa",
        sa.Column(
            "iscrizione_id",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "flussi_cassa",
        sa.Column(
            "trasferimento_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_flussi_cassa_iscrizione_id",
        "flussi_cassa",
        "iscrizioni",
        ["iscrizione_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_flussi_cassa_iscrizione_id", "flussi_cassa", type_="foreignkey"
    )
    op.drop_column("flussi_cassa", "trasferimento_id")
    op.drop_column("flussi_cassa", "iscrizione_id")
    op.drop_column("flussi_cassa", "tipo")
    tipo_flusso_cassa.drop(op.get_bind(), checkfirst=True)
