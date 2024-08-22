let countdown;

document.addEventListener('DOMContentLoaded', () => {
    const resultDiv = document.getElementById('result');
    const topRowCells = document.querySelectorAll('#top-row .cell');

    // Load player name from local storage
    const playerNameInput = document.getElementById('playername');
    const savedName = localStorage.getItem('playerName');
    if (savedName) {
        playerNameInput.value = savedName;
    }

    playerNameInput.addEventListener('blur', () => {
        localStorage.setItem('playerName', playerNameInput.value);
    });

    // Toggle which form works
    const newGameForm = document.getElementById('newGameForm');
    const submitGuessForm = document.getElementById('submitGuessForm');

    newGameForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const playername = document.getElementById("playername").value;
        var checkedRadioButton = document.querySelector('input[name="mode"]:checked');

        disableForm(newGameForm);
        const guessInput = document.getElementById('guessInput')
        guessInput.value = ''
        resultDiv.innerHTML = ''

        var requestData = {
                playername: playername,
                mode: checkedRadioButton.value
            };

        const newGameUrl = document.getElementById('newGameForm').dataset.newGameUrl;

        fetch(newGameUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
        })
        .then(
            response => {
                console.log(response)
                return response.json();
        })
        .then(data => {
            const puzzleSpecific = document.getElementById('puzzleSpecific')
            console.log(puzzleSpecific)
            puzzleSpecific.innerHTML = data.html

            showTopRowLettersAsCapitals()
            makeTopRowClickable()
        })


        enableForm(submitGuessForm);
                    // Timer countdown
        let timer = document.getElementById('timer');
        let time = 120; // 2 minutes in seconds
        countdown = setInterval(() => {
            if (time <= 0) {
                clearInterval(countdown);
                alert('Time is up!');
                return;
            }
            time--;
            const minutes = Math.floor(time / 60);
            const seconds = time % 60;
            timer.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }, 1000);


    });

    submitGuessForm.addEventListener('submit', function(event) {
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
        // Check if the expected properties are in the response
        const answer = data.answer;
        const correct = data.correct;

        // Create HTML content based on the response
        let resultHtml = '';
        if (correct) {
            resultHtml += '<p>Correct!</p>';
        } else {
            resultHtml += '<p>Incorrect!</p>';
        }
            resultHtml += `<p>The answer is "${answer}"</p>`;
        resultDiv.innerHTML = resultHtml;
    }

    function showTopRowLettersAsCapitals() {

        const topRowCells = document.querySelectorAll('#top-row .cell');
        topRowCells.forEach(cell => {
            const letter = cell.textContent.toLowerCase() === 'i' ? 'i' : cell.textContent.toUpperCase();
            cell.textContent = letter
        });
    }


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
        const letter = letterData.true_letter.toLowerCase() === 'i' ? 'i' : letterData.true_letter.toUpperCase();
        cellLowerRow.textContent = letterData.correct ? letter : "?";
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

function submitGuess() {
    clearInterval(countdown);
    disableSubmitButton();
    makeTopRowNonClickable();

    const guess = document.getElementById('submitButton').value;
    fetch('/guess', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ guess }),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('result').textContent = data.result;
    });
}
