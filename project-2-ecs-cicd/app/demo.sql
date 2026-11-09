CREATE TABLE IF NOT EXISTS demo_reservations (
    id INTEGER PRIMARY KEY,
    event_name VARCHAR(64) NOT NULL
);
INSERT INTO demo_reservations (id, event_name)
SELECT 1, 'Portfolio rehearsal'
WHERE NOT EXISTS (SELECT 1 FROM demo_reservations WHERE id = 1);
