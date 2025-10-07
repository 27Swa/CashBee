function showMessage(event) {
    event.preventDefault();
    // validating that data exists
    const name = document.querySelector('input[type="text"]').value.trim();
    const email = document.querySelector('input[type="email"]').value.trim();
    const message = document.querySelector('textarea').value.trim();

    document.querySelector(".overlay").style.display = "block";
    if (!name || !email || !message) {
        document.querySelector(".message.fail").style.display = "block";
    }
    else
        document.querySelector(".message.success").style.display = "block";

}

function closeMessage() {
    document.querySelector(".overlay").style.display = "none";
    document.querySelector(".message.success").style.display = "none";
    document.querySelector(".message.fail").style.display = "none";
} 