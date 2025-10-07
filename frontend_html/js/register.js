document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('signupForm');

    form.addEventListener('submit', function (event) {
        event.preventDefault(); // Stop the form from submitting normally

        // Simple check to ensure fields aren't completely empty (though 'required' handles this)
        const orgName = document.getElementById('orgName').value;
        const orgEmail = document.getElementById('orgEmail').value;

        if (orgName && orgEmail) {
            alert('Sign Up Form Submitted! (No backend functionality)');
            // In a real application, you would send data to the server here:
            // fetch('/api/signup', { method: 'POST', body: new FormData(form) })
            // .then(response => ...)
        } else {
            alert('Please fill out all required fields.');
        }
    });
});