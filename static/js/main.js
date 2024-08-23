let resultDiv, newGameForm, submitGuessForm, timerElement, countdown;
function disableForm(form) {
    Array.from(form.elements).forEach(element => {
        element.disabled = true;
    });
}

function enableForm(form) {
    Array.from(form.elements).forEach(element => {
        element.disabled = false;
    });
}

function updateResultDiv(data) {
    const answer = data.answer;
    const correct = data.correct;

    let resultHtml = '';
    if (correct) {
        resultHtml += '<p>Correct!</p>';
    } else {
        resultHtml += '<p>Incorrect!</p>';
    }
    resultHtml += `<p>The answer is "${answer}"</p>`;
    resultDiv.innerHTML = resultHtml;
}

function capitalizeLetterExceptI(letter) {
    return letter.toLowerCase() === 'i' ? 'i' : letter.toUpperCase();
}

function capitalizePuzzleLetters(selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(element => {
        element.textContent = capitalizeLetterExceptI(element.textContent);
    });
}

function disableClickabilityCell(pos) {
    const cell = document.getElementById(`upperrow-${pos}`);
    cell.classList.remove('clickable');
    cell.classList.add('non-clickable');
    cell.removeEventListener('click', buyLetterEvent);
}

function disableSubmitButton() {
    const submitButton = document.getElementById('submitButton');
    submitButton.disabled = true;
    submitButton.style.cursor = 'not-allowed';
}

function makeTopRowNonClickable() {
    const topRowCells = document.querySelectorAll('#top-row .cell');
    topRowCells.forEach(cell => {
        const pos = cell.getAttribute('data-pos');
        disableClickabilityCell(pos);
    });
}

function makeTopRowClickable() {
    const topRowCells = document.querySelectorAll('#top-row .cell');
    topRowCells.forEach(cell => {
        cell.addEventListener('click', buyLetterEvent);
        if (cell.textContent.trim() === "-") {
            const pos = cell.getAttribute('data-pos');
            disableClickabilityCell(pos);
        }
    });
}

function setupGameForm({ hasMode, puzzleLettersQuery, toprowFunctions }) {
    const timerDuration = parseInt(timerElement.dataset.duration);

    newGameForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const playername = document.getElementById("playername").value;
        let requestData = { playername: playername };

        if (hasMode) {
            const checkedRadioButton = document.querySelector('input[name="mode"]:checked');
            requestData.mode = checkedRadioButton.value;
        }

        disableForm(newGameForm);
        document.getElementById('guessInput').value = '';
        resultDiv.innerHTML = '';

        const newGameUrl = newGameForm.dataset.newGameUrl;

        fetch(newGameUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData),
        })
            .then(response => response.json())
            .then(data => {
                const puzzleSpecific = document.getElementById('puzzlespecific');
                puzzleSpecific.innerHTML = data.html;
                capitalizePuzzleLetters(puzzleLettersQuery)
                if (toprowFunctions) {
                    makeTopRowClickable();
                }
            });

        enableForm(submitGuessForm);

        let time = timerDuration;
        countdown = setInterval(() => {
            if (time <= 0) {
                clearInterval(countdown);
                alert('Time is up!');
                return;
            }
            time--;
            const minutes = Math.floor(time / 60);
            const seconds = time % 60;
            timerElement.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }, 1000);
    });
}

function handleSubmit() {
    submitGuessForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const guess = document.getElementById('guessInput').value;
        clearInterval(countdown);
        disableForm(submitGuessForm);
        makeTopRowNonClickable();
        enableForm(newGameForm);

        const submitGuessUrl = document.getElementById('submitGuessForm').dataset.submitGuessUrl;

        fetch(submitGuessUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ guess }),
        })
            .then(response => response.json())
            .then(data => {
                updateResultDiv(data);
            })

    });
}

document.addEventListener('DOMContentLoaded', () => {
    resultDiv = document.getElementById('result');
    newGameForm = document.getElementById('newGameForm');
    submitGuessForm = document.getElementById('submitGuessForm');
    timerElement = document.getElementById('timer');

    const playerNameInput = document.getElementById('playername');
    const savedName = localStorage.getItem('playerName');
    if (savedName) {
        playerNameInput.value = savedName;
    }

    playerNameInput.addEventListener('blur', () => {
        localStorage.setItem('playerName', playerNameInput.value);
    });

    handleSubmit()

});

function buyLetterEvent(event) {
    const pos = event.currentTarget.getAttribute('data-pos');
    buyLetter(pos);
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
