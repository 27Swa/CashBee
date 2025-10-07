function showMessage(event, button) {
    event.preventDefault();

    // validating that data exists
    const form = button.closest("form");
    const inputs = form.querySelectorAll('input[required]');
    let allFilled = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            allFilled = false;
        }
    });

    document.querySelector(".overlay").style.display = "block";
    if (!allFilled) {
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