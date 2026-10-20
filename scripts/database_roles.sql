-- Run as migration administrator. Set passwords through your secret manager, not this file.
-- The roles have NOLOGIN until an operator explicitly provisions credentials.
DO $$ BEGIN CREATE ROLE company_api NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE company_worker NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE company_watchtower NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
GRANT USAGE ON SCHEMA public TO company_api,company_worker,company_watchtower;
GRANT SELECT,INSERT,UPDATE ON ALL TABLES IN SCHEMA public TO company_api;
REVOKE UPDATE ON audit_records,events,agent_roles FROM company_api;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO company_api,company_worker,company_watchtower;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO company_worker,company_watchtower;
GRANT INSERT,UPDATE ON tasks,task_dependencies,agent_runs,artifacts,budget_reservations,usage_ledger,messages,notification_deliveries,outbox,incidents,revenue_opportunities,decisions,tool_calls,sandboxes TO company_worker;
GRANT INSERT ON events,audit_records TO company_worker,company_watchtower;
GRANT UPDATE (audit_head,stopped) ON organizations TO company_worker,company_watchtower;
GRANT INSERT,UPDATE ON incidents,messages,notification_deliveries,outbox TO company_watchtower;
GRANT UPDATE (status,error) ON tasks TO company_watchtower;
GRANT UPDATE (status) ON agent_runs TO company_watchtower;
GRANT UPDATE (data) ON sandboxes TO company_watchtower;
-- Neither worker role can change owner policy, budgets, role capabilities or approvals.
GRANT INSERT,UPDATE ON decisions TO company_watchtower;
