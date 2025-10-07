"""Add AI triage fields - embedding and user preferences

Revision ID: 003
Revises: 002
Create Date: 2025-10-07

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Add embedding column to emails table
    # text-embedding-3-small produces 1536 dimensions
    op.add_column('emails', sa.Column('embedding', Vector(1536)))

    # Add index for vector similarity search using cosine distance
    op.execute("""
        CREATE INDEX idx_emails_embedding
        ON emails
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # Add user preferences column to users table
    op.add_column('users', sa.Column('preferences', sa.JSON, server_default='{}'))


def downgrade() -> None:
    # Drop index
    op.execute('DROP INDEX IF EXISTS idx_emails_embedding')

    # Remove columns
    op.drop_column('emails', 'embedding')
    op.drop_column('users', 'preferences')

    # Drop pgvector extension (optional, comment out if other tables use it)
    # op.execute('DROP EXTENSION IF EXISTS vector')
