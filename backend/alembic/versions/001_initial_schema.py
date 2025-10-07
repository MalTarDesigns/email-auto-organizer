"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-10-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Users Table
    op.create_table(
        'users',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('email_provider', sa.String(50)),
        sa.Column('access_token', sa.Text),
        sa.Column('refresh_token', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Emails Table
    op.create_table(
        'emails',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID, sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('message_id', sa.String(255), unique=True, nullable=False),
        sa.Column('subject', sa.Text),
        sa.Column('sender_email', sa.String(255)),
        sa.Column('sender_name', sa.String(255)),
        sa.Column('body_text', sa.Text),
        sa.Column('body_html', sa.Text),
        sa.Column('received_at', sa.TIMESTAMP),
        sa.Column('processed_at', sa.TIMESTAMP),
        sa.Column('category', sa.String(50)),
        sa.Column('priority', sa.String(20)),
        sa.Column('urgency_score', sa.DECIMAL(3, 2)),
        sa.Column('sentiment', sa.String(20)),
        sa.Column('requires_action', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Add vector column for embeddings
    op.execute('ALTER TABLE emails ADD COLUMN embedding vector(1536)')

    # Create indexes for emails
    op.create_index('idx_user_received', 'emails', ['user_id', sa.text('received_at DESC')])
    op.create_index('idx_category', 'emails', ['category'])
    op.create_index('idx_priority', 'emails', ['priority'])

    # Email Classifications Table
    op.create_table(
        'email_classifications',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email_id', UUID, sa.ForeignKey('emails.id', ondelete='CASCADE')),
        sa.Column('classification_type', sa.String(50)),
        sa.Column('classification_value', sa.String(100)),
        sa.Column('confidence_score', sa.DECIMAL(3, 2)),
        sa.Column('model_version', sa.String(50)),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Generated Responses Table
    op.create_table(
        'generated_responses',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email_id', UUID, sa.ForeignKey('emails.id', ondelete='CASCADE')),
        sa.Column('response_text', sa.Text, nullable=False),
        sa.Column('tone', sa.String(50)),
        sa.Column('length', sa.String(20)),
        sa.Column('model_used', sa.String(50)),
        sa.Column('generation_timestamp', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('user_approved', sa.Boolean),
        sa.Column('user_edited', sa.Boolean, server_default='false'),
        sa.Column('final_response', sa.Text),
        sa.Column('sent_at', sa.TIMESTAMP),
        sa.Column('feedback_score', sa.Integer),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Create index for generated responses
    op.create_index('idx_email_responses', 'generated_responses', ['email_id', sa.text('generation_timestamp DESC')])

    # User Preferences Table
    op.create_table(
        'user_preferences',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID, sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True),
        sa.Column('auto_triage_enabled', sa.Boolean, server_default='true'),
        sa.Column('auto_respond_enabled', sa.Boolean, server_default='false'),
        sa.Column('response_tone', sa.String(50), server_default="'professional'"),
        sa.Column('priority_rules', JSONB),
        sa.Column('category_rules', JSONB),
        sa.Column('blacklist_senders', ARRAY(sa.Text)),
        sa.Column('whitelist_senders', ARRAY(sa.Text)),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Feedback & Learning Table
    op.create_table(
        'user_feedback',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID, sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('email_id', UUID, sa.ForeignKey('emails.id', ondelete='CASCADE')),
        sa.Column('response_id', UUID, sa.ForeignKey('generated_responses.id', ondelete='SET NULL')),
        sa.Column('feedback_type', sa.String(50)),
        sa.Column('corrected_category', sa.String(50)),
        sa.Column('corrected_priority', sa.String(20)),
        sa.Column('rating', sa.Integer),
        sa.Column('comments', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Add check constraint for rating
    op.create_check_constraint(
        'ck_rating_range',
        'user_feedback',
        'rating BETWEEN 1 AND 5'
    )

    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Add triggers for updated_at columns
    op.execute("""
        CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_user_preferences_updated_at
        BEFORE UPDATE ON user_preferences
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_users_updated_at ON users')
    op.execute('DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences')

    # Drop trigger function
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')

    # Drop tables in reverse order
    op.drop_table('user_feedback')
    op.drop_table('user_preferences')
    op.drop_table('generated_responses')
    op.drop_table('email_classifications')
    op.drop_table('emails')
    op.drop_table('users')

    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS vector')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
