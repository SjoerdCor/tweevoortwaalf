document.addEventListener('DOMContentLoaded', () => {
    setupGameForm({
        puzzleLettersQuery: '#top-row .cell',
        toprowFunctions: true,
        canBuyLetters: true,
    });
}
);