## Task

Build a tiny SQL engine in Python that runs queries over CSV files: SELECT with expressions, WHERE, ORDER BY, LIMIT, GROUP BY with COUNT/SUM/AVG, and an inner JOIN between two files. It should work as a CLI and give useful errors for bad queries.

## Follow-up (send after the first turn is done and committed)

Add Parquet files as a source and a LEFT JOIN. Make queries with a WHERE on a sorted column skip work instead of scanning everything.
