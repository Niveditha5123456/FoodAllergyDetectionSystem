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

function handleSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(document.getElementById("allergyForm"));
    
    fetch("/", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => displayResult(data))
    .catch(error => {
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
    });
}

function displayResult(data) {
    let detected = data.detected || [];

    let resultBox = document.getElementById("resultBox");
    let list = document.getElementById("allergenList");
    let riskText = document.getElementById("riskLevel");

    let totalCount = document.getElementById("totalCount");
    let allergenCount = document.getElementById("allergenCount");
    let safetyPercent = document.getElementById("safetyPercent");

    // 5️⃣ Clear old results
    list.innerHTML = "";

    // 6️⃣ Show detected allergens with proper formatting
    if (detected.length === 0) {
        let li = document.createElement("li");
        li.textContent = "No allergens detected";
        li.style.color = "green";
        li.style.fontWeight = "bold";
        list.appendChild(li);
    } else {
        detected.forEach(function(item) {
            let li = document.createElement("li");
            li.textContent = item.charAt(0).toUpperCase() + item.slice(1);
            li.style.color = "#333";
            li.style.marginBottom = "8px";
            li.style.fontSize = "16px";
            list.appendChild(li);
        });
    }

    // 7️⃣ Risk Logic - Get from server response
    let risk = data.risk || "Safe";
    
    // Normalize risk value for display
    let riskDisplay = risk.toLowerCase();
    if (riskDisplay === "safe") riskDisplay = "Safe";
    else if (riskDisplay === "medium") riskDisplay = "Medium";
    else if (riskDisplay === "high") riskDisplay = "High";

    riskText.textContent = riskDisplay;

    // Color logic
    riskText.classList.remove("safe", "medium", "high");
    if (riskDisplay === "Safe") riskText.classList.add("safe");
    else if (riskDisplay === "Medium") riskText.classList.add("medium");
    else if (riskDisplay === "High") riskText.classList.add("high");

    // 8️⃣ Statistics Panel
    let totalIngredients = data.total_ingredients || 0;
    let allergenDetected = detected.length;
    let safety = Math.round(data.safety_percent || 0);

    totalCount.textContent = totalIngredients;
    allergenCount.textContent = allergenDetected;
    safetyPercent.textContent = safety + "%";

    // 9️⃣ Show Result Section
    resultBox.style.display = "block";
}
