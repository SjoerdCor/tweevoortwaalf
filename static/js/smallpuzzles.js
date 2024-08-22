document.addEventListener('DOMContentLoaded', () => {
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
    const resultDiv = document.getElementById('result');

    newGameForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const playername = document.getElementById("playername").value;

        disableForm(newGameForm);
        enableForm(submitGuessForm);
        const guessInput = document.getElementById('guessInput')
        guessInput.value = ''
        resultDiv.innerHTML = ''

        const newGameUrl = document.getElementById('newGameForm').dataset.newGameUrl;

        fetch(newGameUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ playername }),
        })
        .then(
            response => {
                return response.json();
        })
        .then(data => {
            const puzzleSpecific = document.getElementById('puzzlespecific')
            puzzleSpecific.innerHTML = data.html
        })
    });

    submitGuessForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const guess = document.getElementById('guessInput').value;
        disableForm(submitGuessForm);
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

});
