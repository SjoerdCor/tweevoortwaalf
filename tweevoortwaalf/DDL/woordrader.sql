CREATE SCHEMA IF NOT EXISTS woordrader;

CREATE TABLE IF NOT EXISTS  woordrader.games (
    game_id SERIAL PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    answer CHAR(12) NOT NULL,
    playername VARCHAR(15),
    p_unknown NUMERIC(3, 2) NOT NULL,
    p_wrong NUMERIC(3, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS woordrader.shownletters (
    letterplacement_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES woordrader.games(game_id) ON DELETE CASCADE,
    position INT NOT NULL,
    shown_letter CHAR(1) NOT NULL,
    correct BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS woordrader.guesses (
    guess_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES woordrader.games(game_id) ON DELETE CASCADE,
    guess_time TIMESTAMP NOT NULL,
    guess VARCHAR(15) NOT NULL,
    correct BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS woordrader.boughtletters (
    buyevent_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES woordrader.games(game_id) ON DELETE CASCADE,
    letterposition INT NOT NULL,
    buytime TIMESTAMP NOT NULL
);
