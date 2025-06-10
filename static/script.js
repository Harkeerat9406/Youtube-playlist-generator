function handlePrompt() {
    const user_prompt = document.getElementById('promptInput').value;
    if (user_prompt.trim()) {
        fetch('/extract_music_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({prompt: user_prompt})
        })

        .then(response => response.json())

        .then(data => {
            console.log(data);
            alert('Extracted data: ' + JSON.stringify(data, null, 2))
        })
        
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Check console for details')
        });
    } 
    
    else {
        alert('Please enter a valid prompt!');
    }
}