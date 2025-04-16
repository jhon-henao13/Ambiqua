"""add name to systems

Revision ID: add_name_to_systems
Revises: 
Create Date: 2024-03-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_name_to_systems'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('systems', sa.Column('name', sa.String(100), nullable=False))

def downgrade():
    op.drop_column('systems', 'name') 