# Gemini AI PDF Invoice Extractor (Streamlit)

This Streamlit application allows users to upload PDF invoices and extract structured data using Google's Gemini AI. The extracted information is defined by a Pydantic schema, displayed in a user-friendly table, and can be downloaded as an Excel file.

## Features

*   **PDF Invoice Upload:** Upload one or more PDF files through the Streamlit interface.
*   **API Key Input:** Securely enter your Google Gemini API key directly in the application's sidebar.
*   **Configurable Model ID:** Specify the Gemini model ID you wish to use (defaults to `gemini-1.5-flash-latest`).
*   **Structured Data Extraction:** Utilizes Gemini's function calling/schema-based extraction capabilities to parse invoices according to a predefined Pydantic model (`Invoice` and `LineItem`).
*   **Data Display:** Presents the extracted data in an interactive table within the app.
*   **Excel Export:** Download the summarized extracted data as an `.xlsx` file.
*   **Temporary File Handling:** Manages temporary storage of uploaded files for processing.
*   **Gemini File API Management:** Uploads files to Gemini's File API and attempts to delete them after processing to manage resources.

## Prerequisites

*   Python 3.8 or higher
*   `pip` (Python package installer)
*   A Google Gemini API Key. You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repository-name.git
    cd your-repository-name
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    Create a `requirements.txt` file with the following content:
    ```txt
    streamlit
    pandas
    openpyxl
    pydantic
    google-genai
    ```
    Then install them:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

*   **Gemini API Key:** This is entered directly into the application's sidebar when you run it. It is not stored in any configuration files.
*   **Gemini Model ID:** The application defaults to `gemini-1.5-flash-latest`. You can change this in the sidebar if you have access to other compatible models (e.g., `gemini-1.5-pro-latest`). Ensure the model supports schema-based JSON output.

## Usage

1.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```

2.  **Open the application in your browser:**
    Streamlit will typically open the app automatically, or provide a local URL (e.g., `http://localhost:8501`).

3.  **Enter your Gemini API Key** in the sidebar.

4.  **(Optional)** Change the Gemini Model ID in the sidebar if needed.

5.  **Upload PDF invoice files** using the file uploader.

6.  Click the **"🚀 Process Invoices"** button.

7.  View the extracted data in the table.

8.  Click the **"📥 Download Summary as Excel"** button to save the results.

## File Structure

```
.
├── app.py              # The main Streamlit application script
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Technology Stack

*   **Streamlit:** For the web application interface.
*   **Python:** Core programming language.
*   **Google Gemini API:** For the AI-powered data extraction.
    *   `google-genai` library: The official Google Generative AI SDK for Python.
*   **Pydantic:** For data validation and schema definition.
*   **Pandas:** For data manipulation and creating the Excel output.
*   **Openpyxl:** For writing to Excel files.

## Important Notes

*   **API Costs:** Using the Gemini API may incur costs depending on your usage and Google's pricing model. Be mindful of the number and size of documents you process.
*   **Extraction Accuracy:** The accuracy of the extracted data depends on the quality of the PDF, the clarity of the invoice layout, and the capabilities of the chosen Gemini model. The prompt used for extraction can also be further optimized.
*   **Gemini File API:** The application attempts to delete files uploaded to the Gemini File API after processing. Monitor your Gemini project to ensure files are managed correctly, especially if errors occur during deletion.
*   **Error Handling:** Basic error handling is implemented. For production use, more robust error handling and logging might be necessary.

## Contributing

Contributions are welcome! If you have suggestions for improvements or find any issues, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details (if you choose to add one).
*(Suggestion: If you don't have a LICENSE.md, you can simply state "This project is licensed under the MIT License.")*

---

Happy extracting!
```
