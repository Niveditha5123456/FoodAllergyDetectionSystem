Food Allergy Detection System:
The Food Allergy Detection System is a web-based application that helps users identify potential allergens present in packaged food products.
The system uses OCR (Optical Character Recognition) to extract ingredient text from uploaded food label images and compares it with predefined allergen categories to determine risk levels.
This project is designed to improve food safety awareness and assist individuals with mild, moderate, or severe allergies in making informed dietary decisions.

Key Features:
Image Upload & OCR Scanning (Tesseract OCR),
Allergen Detection using keyword mapping,
Severity Classification (Safe / Mild / Severe),
Color-coded Risk Display
🟢 Green → Safe
🟡 Yellow → Medium
🔴 Red → High,
Status Panel showing:
Total Ingredients
Allergens Detected
Safety Percentage

Technologies Used:
Frontend: HTML, CSS, JavaScript.
Backend: Python (Flask).
OCR Engine: PyTesseract.
Database: SQLite3.
Version Control: Git & GitHub.

 How It Works:
User uploads a food label image.
OCR extracts ingredient text.
System matches ingredients with allergen categories.
Risk level is calculated based on detected allergens.
Results are displayed with severity color coding and statistics

 Future Enhancements:
AI-based ingredient recognition improvement,
User profile with personal allergy storage,
Real-time barcode scanning,
Cloud database integration,
Mobile application version
