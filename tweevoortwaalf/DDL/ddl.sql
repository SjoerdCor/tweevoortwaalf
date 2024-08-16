CREATE SCHEMA IF NOT EXISTS woordrader;

CREATE TABLE woordrader.games (
    game_id SERIAL PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    answer CHAR(12) NOT NULL,
    mode VARCHAR(50) NOT NULL
);

CREATE TABLE woordrader.shownletters (
    letterplacement_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES woordrader.games(game_id) ON DELETE CASCADE,
    position INT NOT NULL,
    shown_letter CHAR(1) NOT NULL,
    correct BOOLEAN NOT NULL
);
