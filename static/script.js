function handlePrompt() {
    const user_prompt = document.getElementById('promptInput').value.trim();

    if (!user_prompt) {
        alert('Please enter a valid prompt!');
        return;
    }

    // Step 1: Check if user is logged in
    fetch('/is_logged_in')
        .then(res => res.json())
        .then(status => {
            if (!status.logged_in) {
                // Not logged in → redirect to login
                window.location.href = '/login';
            } else {
                // Logged in → proceed
                fetch('/extract_music_data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ prompt: user_prompt })
                })
                .then(async response => {
                    if (!response.ok) {
                        if (response.status === 401) {
                            // Still not authenticated somehow → redirect
                            window.location.href = '/login';
                        } else {
                            throw new Error('Server error');
                        }
                    }

                    const data = await response.json();
                    console.log(data);
                    document.getElementById('resultDisplay').textContent = JSON.stringify(data, null, 2);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred. Check console for details');
                });
            }
        });
}
