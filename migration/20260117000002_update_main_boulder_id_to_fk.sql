ALTER TABLE boulder
ADD CONSTRAINT fk_boulder_main_boulder
FOREIGN KEY (main_boulder_id)
REFERENCES boulder(id)
ON DELETE SET NULL;

CREATE INDEX idx_boulder_main_boulder_id ON boulder(main_boulder_id);
