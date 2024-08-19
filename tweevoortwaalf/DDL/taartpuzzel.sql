CREATE SCHEMA IF NOT EXISTS taartpuzzel;

CREATE TABLE IF NOT EXISTS  taartpuzzel.games (
    game_id SERIAL PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    answer CHAR(9) NOT NULL,
    startpoint INT NOT NULL,
    direction INT NOT NULL,
    missing_letter_index INT NOT NULL,
    playername VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS taartpuzzel.guesses (
    guess_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES taartpuzzel.games(game_id) ON DELETE CASCADE,
    guess_time TIMESTAMP NOT NULL,
    guess VARCHAR(12) NOT NULL,
    correct BOOLEAN NOT NULL
);
