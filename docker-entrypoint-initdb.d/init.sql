-- Make test DB --
SELECT 'CREATE DATABASE movies_test_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'movies_test_db')\gexec