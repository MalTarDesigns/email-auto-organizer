"""Add Google auth fields and update schema

Revision ID: 002
Revises: 001
Create Date: 2025-10-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add google_id to users table
    op.add_column('users', sa.Column('google_id', sa.String(255), unique=True))
    op.create_index('idx_google_id', 'users', ['google_id'])

    # Add token_expires_at to users table
    op.add_column('users', sa.Column('token_expires_at', sa.TIMESTAMP))

    # Make access_token and refresh_token not nullable for new records
    # Note: Existing records will need to be updated manually

    # Update email_classifications table structure to match new model
    op.add_column('email_classifications', sa.Column('category', sa.String(50)))
    op.add_column('email_classifications', sa.Column('priority', sa.String(20)))
    op.add_column('email_classifications', sa.Column('urgency_score', sa.DECIMAL(3, 2)))
    op.add_column('email_classifications', sa.Column('sentiment', sa.String(20)))
    op.add_column('email_classifications', sa.Column('reasoning', sa.Text))
    op.add_column('email_classifications', sa.Column('metadata', sa.JSON))

    # Update emails table - add updated_at column
    op.add_column('emails', sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')))

    # Add trigger for emails updated_at
    op.execute("""
        CREATE TRIGGER update_emails_updated_at
        BEFORE UPDATE ON emails
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # Add index for sender_email
    op.create_index('idx_sender_email', 'emails', ['sender_email'])

    # Add index for message_id
    op.create_index('idx_message_id', 'emails', ['message_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_google_id', 'users')
    op.drop_index('idx_sender_email', 'emails')
    op.drop_index('idx_message_id', 'emails')

    # Drop trigger
    op.execute('DROP TRIGGER IF EXISTS update_emails_updated_at ON emails')

    # Remove columns from users
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'token_expires_at')

    # Remove columns from email_classifications
    op.drop_column('email_classifications', 'category')
    op.drop_column('email_classifications', 'priority')
    op.drop_column('email_classifications', 'urgency_score')
    op.drop_column('email_classifications', 'sentiment')
    op.drop_column('email_classifications', 'reasoning')
    op.drop_column('email_classifications', 'metadata')

    # Remove columns from emails
    op.drop_column('emails', 'updated_at')
