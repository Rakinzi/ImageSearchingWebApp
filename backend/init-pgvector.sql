-- Initialize pgvector extension for PostgreSQL
-- This script runs automatically when PostgreSQL container starts for the first time

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
