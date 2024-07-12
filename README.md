# Twee Voor Twaalf
This repository contains the code to play all games from the Dutch game show Twee voor Twaalf:

* The Paardensprong: a puzzle in which 8 letters are reordered so that only the knight jumps
recreate a word - which must be guessed
* The Taartpuzzel: a puzzle in which 9 letters are shown as part of a pie, with one letter
missing. The word can go either way around the circle, and must be guessed
* The Woordrader, which is the anagram game at the end of the game show, in which
12 letters are shown, some of which may be missing and others of which may be wrong. One can buy letters
so they are shown in the correct place. THe aim is to guess the 12 letter word while buying as few 
letters as possible

This repository improves on other options on the internet to play these games in two ways
* The word list is much better, taking only nouns and actually existing words into account
* The Woordrader/anagram game was not available including buying letters

## Installation guide
Clone this repo. 

This package can be installed by running `pip install .` .
To also be able to run the word analysis, run `pip install .[analysis]`

You can run the woordrader web-app by running  `python app.py`; this requires a 
FLASK_SECRET_KEY in the environment. This is most easily done by creating a file
`.env` containing `FLASK_SECRET_KEY=your_secret_key_here`