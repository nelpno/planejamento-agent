-- Migration: Adicionar colunas de direcionamento do mes na tabela planejamentos
-- Data: 2026-03-15
-- Descricao: Separa PERFIL DO CLIENTE (Kick Off) de DIRECIONAMENTO DO MES (Planejamento)

ALTER TABLE planejamentos ADD COLUMN IF NOT EXISTS produtos_promover TEXT;
ALTER TABLE planejamentos ADD COLUMN IF NOT EXISTS referencias_anteriores TEXT;
ALTER TABLE planejamentos ADD COLUMN IF NOT EXISTS feedback_reuniao TEXT;
