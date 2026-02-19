-- Broward Health AI Content System - Database Schema
-- Run this in Supabase SQL Editor

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profiles (users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT,
  role TEXT DEFAULT 'staff' CHECK (role IN ('staff', 'doctor', 'admin')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Categories
CREATE TABLE IF NOT EXISTS categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(100) NOT NULL,
  color VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Drafts (blog posts)
CREATE TABLE IF NOT EXISTS drafts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(500),
  slug VARCHAR(500),
  category_id UUID REFERENCES categories(id),
  content TEXT,
  excerpt TEXT,
  author_name VARCHAR(200),
  author_credentials VARCHAR(200),
  meta_description VARCHAR(200),
  hero_image_url TEXT,
  read_time_minutes INTEGER DEFAULT 5,
  seo_score INTEGER DEFAULT 0,
  llm_score INTEGER DEFAULT 0,
  workflow_status VARCHAR(50) DEFAULT 'draft' 
    CHECK (workflow_status IN (
      'draft', 'generating', 'ai_review', 'staff_review', 
      'doctor_review', 'approved', 'publishing', 'published'
    )),
  source VARCHAR(50) DEFAULT 'manual',
  created_by UUID REFERENCES profiles(id),
  published_by UUID REFERENCES profiles(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  published_at TIMESTAMPTZ
);

-- Draft sections
CREATE TABLE IF NOT EXISTS draft_sections (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  draft_id UUID REFERENCES drafts(id) ON DELETE CASCADE,
  h2 VARCHAR(300),
  content TEXT,
  order_index INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Published content
CREATE TABLE IF NOT EXISTS published (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  draft_id UUID REFERENCES drafts(id),
  published_url VARCHAR(500),
  published_at TIMESTAMPTZ DEFAULT NOW(),
  published_by UUID REFERENCES profiles(id),
  external_id VARCHAR(100)
);

-- Generation requests
CREATE TABLE IF NOT EXISTS generation_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  topic VARCHAR(500),
  category_id UUID REFERENCES categories(id),
  keywords TEXT[],
  status VARCHAR(50) DEFAULT 'pending',
  requested_by UUID REFERENCES profiles(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Agent outputs
CREATE TABLE IF NOT EXISTS agent_outputs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  request_id UUID REFERENCES generation_requests(id) ON DELETE CASCADE,
  agent_name VARCHAR(50),
  input_data JSONB,
  output_data JSONB,
  model_used VARCHAR(50),
  tokens_used INTEGER,
  duration_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Quality gates
CREATE TABLE IF NOT EXISTS quality_gates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  request_id UUID REFERENCES generation_requests(id) ON DELETE CASCADE,
  gate_name VARCHAR(50),
  passed BOOLEAN,
  value JSONB,
  threshold JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reviewer feedback
CREATE TABLE IF NOT EXISTS reviewer_feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  draft_id UUID REFERENCES drafts(id) ON DELETE CASCADE,
  user_id UUID REFERENCES profiles(id),
  role VARCHAR(20),
  decision VARCHAR(20),
  feedback TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed categories
INSERT INTO categories (name, color) VALUES
  ('Cardiac Care', '#E53935'),
  ('Orthopedics', '#1E88E5'),
  ('Pediatrics', '#43A047'),
  ('Cancer Care', '#8E24AA'),
  ('Mental Health', '#FB8C00'),
  ('Emergency Medicine', '#D81B60'),
  ('Primary Care', '#00ACC1'),
  ('Women''s Health', '#F06292'),
  ('Senior Care', '#7986CB'),
  ('Wellness & Prevention', '#26A69A')
ON CONFLICT DO NOTHING;

-- RLS Policies
ALTER TABLE drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_outputs ENABLE ROW LEVEL SECURITY;

-- Allow read access to authenticated users
CREATE POLICY "Allow read drafts" ON drafts
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow read categories" ON categories
  FOR SELECT USING (true);

CREATE POLICY "Allow read generation_requests" ON generation_requests
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow read agent_outputs" ON agent_outputs
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow read quality_gates" ON quality_gates
  FOR SELECT USING (auth.role() = 'authenticated');

-- Allow insert/update for authenticated users
CREATE POLICY "Allow insert drafts" ON drafts
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow update drafts" ON drafts
  FOR UPDATE USING (auth.role() = 'authenticated');
