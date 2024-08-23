document.addEventListener('DOMContentLoaded', () => {
    setupGameForm({
        hasMode: true,
        puzzleLettersQuery: '#top-row .cell',
        toprowFunctions: true
    });
}
);