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
    const link = `https://www.vandale.nl/gratis-woordenboek/nederlands/betekenis/${answer.replace(/\u0133/g, 'ij')}`;
    resultHtml += `<p>The answer is <a href="${link}" target="_blank">${answer}</a></p>`;
    resultDiv.innerHTML = resultHtml;
}

function capitalizeLetterExceptI(letter) {
    return letter.trim().toLowerCase() === 'i' ? letter : letter.toUpperCase();
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

function resetTimer(timerDuration, timerElement) {
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
}

function collapseNewGameForm(playerName, mode) {
    document.querySelector('.player-name-section').style.display = 'none';
    document.getElementById('extraInfoGameSetup').style.display = 'none';

    document.getElementById('displayName').textContent = playerName
    document.getElementById('displayMode').textContent = mode
    document.getElementById('collapsedInfo').style.display = 'block';

}

function expandNewGameForm() {
    document.querySelector('.player-name-section').style.display = 'block';
    document.getElementById('extraInfoGameSetup').style.display = 'block';

    document.getElementById('collapsedInfo').style.display = 'none';
}

function setupGameForm({ puzzleLettersQuery, toprowFunctions, canBuyLetters }) {
    const timerDuration = parseInt(timerElement.dataset.duration);

    newGameForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const playername = document.getElementById("playername").value;
        let requestData = { playername: playername };

        const checkedRadioButton = document.querySelector('input[name="mode"]:checked');
        requestData.mode = checkedRadioButton.value;

        if (canBuyLetters) {
            lettersBoughtCount = 0;
            document.getElementById('letters-bought').textContent = lettersBoughtCount;
        }

        disableForm(newGameForm);
        collapseNewGameForm(playername, requestData.mode)
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
            })
            .then(() => {
                enableForm(submitGuessForm);
                resetTimer(timerDuration, timerElement);

                const guessInput = document.getElementById('guessInput');
                guessInput.focus();
            });

    });
}


document.addEventListener('DOMContentLoaded', () => {
    resultDiv = document.getElementById('result');
    newGameForm = document.getElementById('newGameForm');
    submitGuessForm = document.getElementById('submitGuessForm');
    timerElement = document.getElementById('timer');


    document.querySelector('.menu-icon').addEventListener('click', function () {
        var menu = document.getElementById('menu');
        if (menu.style.display === "none") {
            menu.style.display = "block";
        } else {
            menu.style.display = "none";
        }
    });



    const playerNameInput = document.getElementById('playername');
    const savedName = localStorage.getItem('playerName');
    if (savedName) {
        playerNameInput.value = savedName;
    }

    playerNameInput.addEventListener('blur', () => {
        localStorage.setItem('playerName', playerNameInput.value);
    });

    function addGuessEventListener() {
        submitGuessForm.addEventListener('submit', function (event) {
            event.preventDefault();

            const guess = document.getElementById('guessInput').value;
            clearInterval(countdown);
            disableForm(submitGuessForm);
            makeTopRowNonClickable();
            expandNewGameForm();
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
            const newGameButton = document.getElementById('newGameButton');
            newGameButton.focus();
        });
    }

    addGuessEventListener()

});
