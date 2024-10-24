"""update payment link table. add linkcode

Revision ID: 8daecb0af7fa
Revises: 0a277c807c27
Create Date: 2024-10-24 01:13:04.744000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8daecb0af7fa'
down_revision: Union[str, None] = '0a277c807c27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
