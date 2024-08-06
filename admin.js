document.getElementById('updateTagsForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const hostname = document.getElementById('tagHostname').value;
    const newTags = JSON.parse(document.getElementById('newTags').value);

    try {
        const response = await fetch('/update_tags', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ hostname, tags: newTags }),
        });

        if (response.ok) {
            alert('Tags updated successfully');
        } else {
            const errorData = await response.json();
            alert(`Failed to update tags: ${errorData.error}`);
        }
    } catch (error) {
        console.error('Error updating tags:', error);
        alert('An error occurred while updating tags');
    }
});