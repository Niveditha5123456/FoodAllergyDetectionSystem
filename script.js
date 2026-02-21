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

function showResult() {

    let ingredients = ["milk", "soy", "sugar"]; // sample input
    let userAllergens = ["milk", "soy"];

    let detected = [];

    userAllergens.forEach(function(allergen) {
        if (ingredients.includes(allergen)) {
            detected.push(allergen);
        }
    });

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

    // 7️⃣ Risk Logic (Mild / Moderate / Severe)
    let risk = "Safe";

    if (detected.length === 1) {
        risk = "Medium";
    } 
    else if (detected.length >= 2) {
        risk = "High";
    }

    riskText.textContent = risk;

    // Color logic
    riskText.classList.remove("safe", "medium", "high"); // ← your remove code
    if (risk === "Safe") riskText.classList.add("safe");
    else if (risk === "Medium") riskText.classList.add("medium");
    else riskText.classList.add("high");

    // 8️⃣ Statistics Panel
    let totalIngredients = ingredients.length;
    let allergenDetected = detected.length;

    let safety = Math.round(((totalIngredients - allergenDetected) / totalIngredients) * 100);

    totalCount.textContent = totalIngredients;
    allergenCount.textContent = allergenDetected;
    safetyPercent.textContent = safety + "%";

    // Color logic
    

    // 9️⃣ Show Result Section
    resultBox.style.display = "block";
}