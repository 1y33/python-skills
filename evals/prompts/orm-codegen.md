## Task

Write a small ORM library in Python with code generation: point it at an existing SQLite database and it generates typed Python model classes from the schema, so queries are checked by mypy. Queries should be built in Python (filters, ordering, joins through foreign keys, inserts, updates, deletes) and compile to parameterized SQL. It should also generate a migration when the models change, and regenerating must not destroy code the user wrote by hand next to the generated models.

## Follow-up (send after the first turn is done and committed)

Add PostgreSQL support next to SQLite, including its types (UUID, JSONB, arrays, timestamptz), and loading related rows without one query per row.
