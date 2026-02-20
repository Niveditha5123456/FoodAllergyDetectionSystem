function toggle(id) {
    const element = document.getElementById(id);
    element.classList.toggle("show");
}

/* Optional: Close other dropdowns when one is opened */
document.addEventListener("click", function(event) {
    const dropdowns = document.querySelectorAll(".dropdown-content");

    dropdowns.forEach(function(dropdown) {
        if (!dropdown.parentElement.contains(event.target)) {
            dropdown.classList.remove("show");
        }
    });
});