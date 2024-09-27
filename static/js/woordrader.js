let lettersBoughtCount;

document.addEventListener('DOMContentLoaded', () => {
    setupGameForm({
        puzzleLettersQuery: '#top-row .cell',
        toprowFunctions: true,
        canBuyLetters: true,
    });
}
);

function buyLetterEvent(event) {
    const pos = event.currentTarget.getAttribute('data-pos');
    buyLetter(pos);

    lettersBoughtCount++;
    document.getElementById('letters-bought').textContent = lettersBoughtCount;

    disableClickabilityCell(pos);
}

function buyLetter(quizposition) {
    fetch('/buy_letter', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ quizposition }),
    })
        .then(response => response.json())
        .then(data => {
            const cellUpperRow = document.getElementById(`upperrow-${quizposition}`);
            const cellLowerRow = document.getElementById(`lowerrow-${data[quizposition].answer_position}`);
            const letterData = data[quizposition];

            cellUpperRow.textContent = "";
            const letter = capitalizeLetterExceptI(letterData.true_letter)
            cellLowerRow.textContent = letterData.correct ? letter : "?";
        });
}
