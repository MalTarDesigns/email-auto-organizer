-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    email_provider VARCHAR(50),
    access_token TEXT,
    refresh_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Emails Table
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    subject TEXT,
    sender_email VARCHAR(255),
    sender_name VARCHAR(255),
    body_text TEXT,
    body_html TEXT,
    received_at TIMESTAMP,
    processed_at TIMESTAMP,
    category VARCHAR(50),
    priority VARCHAR(20),
    urgency_score DECIMAL(3,2),
    sentiment VARCHAR(20),
    requires_action BOOLEAN DEFAULT FALSE,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for emails table
CREATE INDEX idx_user_received ON emails(user_id, received_at DESC);
CREATE INDEX idx_category ON emails(category);
CREATE INDEX idx_priority ON emails(priority);

-- Email Classifications Table
CREATE TABLE email_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    classification_type VARCHAR(50),
    classification_value VARCHAR(100),
    confidence_score DECIMAL(3,2),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generated Responses Table
CREATE TABLE generated_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    response_text TEXT NOT NULL,
    tone VARCHAR(50),
    length VARCHAR(20),
    model_used VARCHAR(50),
    generation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_approved BOOLEAN,
    user_edited BOOLEAN DEFAULT FALSE,
    final_response TEXT,
    sent_at TIMESTAMP,
    feedback_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for generated responses
CREATE INDEX idx_email_responses ON generated_responses(email_id, generation_timestamp DESC);

-- User Preferences Table
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    auto_triage_enabled BOOLEAN DEFAULT TRUE,
    auto_respond_enabled BOOLEAN DEFAULT FALSE,
    response_tone VARCHAR(50) DEFAULT 'professional',
    priority_rules JSONB,
    category_rules JSONB,
    blacklist_senders TEXT[],
    whitelist_senders TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Feedback & Learning Table
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    response_id UUID REFERENCES generated_responses(id) ON DELETE SET NULL,
    feedback_type VARCHAR(50),
    corrected_category VARCHAR(50),
    corrected_priority VARCHAR(20),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
