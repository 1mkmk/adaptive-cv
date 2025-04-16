function generateCV() {
    const userInput = document.getElementById('user_input').value;
    const resultDiv = document.getElementById('result');
    
    if (!userInput.trim()) {
        resultDiv.innerText = "Please enter your skills and experience first";
        return;
    }
    
    resultDiv.innerText = "Generating CV...";
    
    fetch('/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: userInput})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            resultDiv.innerText = "Error: " + data.error;
        } else {
            resultDiv.innerText = data.result;
        }
    })
    .catch(error => {
        resultDiv.innerText = "Error: " + error;
    });
}