-- Broward Health AI Content System - Database Schema
-- Run this in Supabase SQL Editor

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
  category_id UUID,
  content TEXT,
  excerpt TEXT,
  author_name VARCHAR(200),
  author_credentials VARCHAR(200),
  meta_description VARCHAR(200),
  hero_image_url TEXT,
  read_time_minutes INTEGER DEFAULT 5,
  seo_score INTEGER DEFAULT 0,
  llm_score INTEGER DEFAULT 0,
  workflow_status VARCHAR(50) DEFAULT 'draft',
  source VARCHAR(50) DEFAULT 'manual',
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

-- Generation requests
CREATE TABLE IF NOT EXISTS generation_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  topic VARCHAR(500),
  category_id UUID,
  keywords TEXT[],
  status VARCHAR(50) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Quality gates
CREATE TABLE IF NOT EXISTS quality_gates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  request_id UUID,
  gate_name VARCHAR(50),
  passed BOOLEAN,
  value JSONB,
  threshold JSONB,
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

-- Disable RLS for now (simplified)
ALTER TABLE drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE draft_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_gates ENABLE ROW LEVEL SECURITY;

-- Allow public access (for demo)
CREATE POLICY "Allow all drafts" ON drafts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all categories" ON categories FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all requests" ON generation_requests FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all sections" ON draft_sections FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all gates" ON quality_gates FOR ALL USING (true) WITH CHECK (true);
