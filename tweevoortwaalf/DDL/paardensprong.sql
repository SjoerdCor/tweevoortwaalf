CREATE SCHEMA IF NOT EXISTS paardensprong;

CREATE TABLE IF NOT EXISTS  paardensprong.games (
    game_id SERIAL PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    answer CHAR(8) NOT NULL,
    startpoint INT NOT NULL,
    direction INT NOT NULL,
    playername VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS paardensprong.guesses (
    guess_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES paardensprong.games(game_id) ON DELETE CASCADE,
    guess_time TIMESTAMP NOT NULL,
    guess VARCHAR(12) NOT NULL,
    correct BOOLEAN NOT NULL,
    UNIQUE (game_id)
);

CREATE TABLE IF NOT EXISTS paardensprong.puzzleoptions (
    option_id SERIAL PRIMARY KEY,
    answer CHAR(8) NOT NULL,
    startpoint INT NOT NULL,
    direction INT NOT NULL,
    probability NUMERIC(5, 4) NOT NULL
);
