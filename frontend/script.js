function handlePrompt() {
    const prompt = document.getElementById('promptInput').value;
    if (prompt.trim()) {
        alert('Creating playlist based on: ' + prompt);
        // Future integration with YouTube API would go here

    } else {
        alert('Please enter a valid prompt!');
    }
}