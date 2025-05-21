import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd
import os
import tempfile # For temporary file handling
import io # For Excel download
from google.genai import types # Added for the new SDK
import asyncio # Added for asynchronous processing

# Try to import google.genai, show error if not found
try:
    from google import genai
except ImportError:
    st.error("The 'google-genai' library is not installed. Please install it by running: pip install google-genai") # Ensured this is correct
    st.stop()

# --- Pydantic Models (as provided) ---
class LineItem(BaseModel):
    description: str
    quantity: float
    gross_worth: float

class Invoice(BaseModel):
    invoice_number: str
    date: str
    gstin: str
    seller_name: str
    buyer_name: str
    buyer_gstin: Optional[str] = None
    line_items: List[LineItem]
    total_gross_worth: float
    cgst: Optional[float] = None
    sgst: Optional[float] = None
    igst: Optional[float] = None
    place_of_supply: Optional[str] = None
    expense_ledger: Optional[str] = None
    tds: Optional[str] = None

# --- Gemini API Interaction Function (Async) ---
async def extract_structured_data(
    client_instance, # The genai.Client object
    gemini_model_id: str,
    file_content: bytes, 
    original_filename: str, 
    pydantic_schema: BaseModel, 
):
    temp_file_path = None
    gemini_file_resource = None 

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_filename)[1]) as tmp:
            tmp.write(file_content)
            temp_file_path = tmp.name
        
        # Verbose st.write calls removed as per subtask
        # st.write(f"Uploading '{original_filename}' (temp: {temp_file_path}) to Gemini File API...") 
        gemini_file_resource = await client_instance.aio.files.upload(path=temp_file_path) 
        # st.write(f"'{original_filename}' uploaded. Gemini file name: {gemini_file_resource.name}")

        prompt = (
            "Extract all relevant and clear information from the invoice, adhering to Indian standards "
            "for dates (DD/MM/YYYY or DD-MM-YYYY) and codes (like GSTIN, HSN/SAC). "
            "Accurately identify the total amount payable. Classify the nature of expense and suggest an "
            "applicable ledger type (e.g., 'Office Supplies', 'Professional Fees', 'Software Subscription'). "
            "Determine TDS applicability (e.g., 'Yes - Section 194J', 'No', 'Uncertain'). "
            "Determine reverse charge GST (RCM) applicability (e.g., 'Yes', 'No', 'Uncertain'). "
            "Handle missing data appropriately by setting fields to null or an empty string where "
            "Optional, and raise an issue if critical data is missing for required fields. "
            "Do not make assumptions or perform calculations beyond what's explicitly stated in the invoice text. "
            "If a value is clearly zero, represent it as 0.0 for floats. For dates, prefer DD/MM/YYYY."
        )
        # st.write(f"Sending '{original_filename}' to Gemini model '{gemini_model_id}' for extraction...")
        response = await client_instance.aio.models.generate_content( 
            model=gemini_model_id,
            contents=[prompt, gemini_file_resource], 
            config=types.GenerateContentConfig(response_mime_type='application/json', response_schema=pydantic_schema)
        )
        # st.write(f"Data extracted for '{original_filename}'.") # Success is handled in main_processing_async
        parsed_model = pydantic_schema.model_validate_json(response.text)
        return parsed_model

    except Exception as e:
        # This error will be caught by asyncio.gather and handled in main_processing_async
        # For detailed debugging, it's good to log it here or re-raise
        # st.error(f"Error processing '{original_filename}' within extract_structured_data: {e}") 
        # import traceback # Keep traceback for debugging if needed, but don't show in UI here
        # st.error(traceback.format_exc())
        raise # Re-raise the exception to be caught by asyncio.gather
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            # st.write(f"Deleted temporary local file: {temp_file_path}") # Removed
        
        if gemini_file_resource and hasattr(client_instance.aio, 'files') and hasattr(client_instance.aio.files, 'delete'):
            try:
                # st.write(f"Attempting to delete '{gemini_file_resource.name}' from Gemini File API...") # Removed
                await client_instance.aio.files.delete(name=gemini_file_resource.name) 
                # st.write(f"Successfully deleted '{gemini_file_resource.name}' from Gemini.") # Removed
            except Exception as e_del:
                st.warning(f"Could not delete '{gemini_file_resource.name}' from Gemini File API: {e_del}") # Keep this warning
        elif gemini_file_resource:
            st.warning(f"Could not determine how to delete Gemini file '{gemini_file_resource.name}'. Manual cleanup may be required.") # Keep this


# --- Streamlit App UI ---
st.set_page_config(layout="wide")
st.title("📄 PDF Invoice Extractor (Gemini AI)")

st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("Enter your Gemini API Key:", type="password")

DEFAULT_GEMINI_MODEL_ID = "gemini-1.5-flash-latest"
gemini_model_id_input = st.sidebar.text_input("Gemini Model ID for Extraction:", DEFAULT_GEMINI_MODEL_ID)
st.sidebar.caption(f"Default is `{DEFAULT_GEMINI_MODEL_ID}`. Your script used 'gemini-2.0-flash'. "
                   "Ensure the model ID is correct and supports schema-based JSON output.")


st.info(
    "**Instructions:**\n"
    "1. Enter your Gemini API Key in the sidebar.\n"
    "2. Optionally, change the Gemini Model ID if needed.\n"
    "3. Upload one or more PDF invoice files.\n"
    "4. Click 'Process Invoices' to extract data.\n"
    "   The extracted data will be displayed in a table and available for download as Excel."
)

uploaded_files = st.file_uploader(
    "Choose PDF invoice files",
    type="pdf",
    accept_multiple_files=True
)

if 'summary_rows' not in st.session_state:
    st.session_state.summary_rows = []
if 'client' not in st.session_state:
    st.session_state.client = None


if st.button("🚀 Process Invoices", type="primary"):
    if not api_key_input:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not uploaded_files:
        st.error("Please upload at least one PDF file.")
    elif not gemini_model_id_input:
        st.error("Please specify a Gemini Model ID in the sidebar.")
    else:
        try:
            st.session_state.client = genai.Client(api_key=api_key_input)
            st.success("Gemini client initialized successfully.")
        except Exception as e:
            st.error(f"Failed to initialize Gemini client: {e}")
            st.session_state.client = None

        if st.session_state.client:
            st.session_state.summary_rows = [] 
            progress_bar = st.progress(0)
            total_files = len(uploaded_files)

            async def main_processing_async():
                tasks = []
                for uploaded_file_obj in uploaded_files:
                    tasks.append(extract_structured_data(
                        client_instance=st.session_state.client,
                        gemini_model_id=gemini_model_id_input,
                        file_content=uploaded_file_obj.getvalue(), 
                        original_filename=uploaded_file_obj.name,    
                        pydantic_schema=Invoice                     
                    ))
                
                with st.spinner(f"Processing {total_files} invoice(s) concurrently... Please wait."):
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                successful_extractions = 0
                for i, result_or_exc in enumerate(results):
                    current_file_name = uploaded_files[i].name
                    st.markdown(f"---") # Separator for each file's result

                    if isinstance(result_or_exc, Exception):
                        st.error(f"⚠️ Error processing **{current_file_name}**: {result_or_exc}")
                    elif result_or_exc:
                        extracted_data = result_or_exc
                        st.success(f"✅ Successfully extracted data from **{current_file_name}**.")
                        successful_extractions +=1
                        
                        cgst = extracted_data.cgst if extracted_data.cgst is not None else 0.0
                        sgst = extracted_data.sgst if extracted_data.sgst is not None else 0.0
                        igst = extracted_data.igst if extracted_data.igst is not None else 0.0
                        pos = extracted_data.place_of_supply if extracted_data.place_of_supply else "N/A"
                        buyer_gstin_display = extracted_data.buyer_gstin or "N/A"
                        narration = (
                            f"Invoice {extracted_data.invoice_number} dated {extracted_data.date} "
                            f"was issued by {extracted_data.seller_name} (GSTIN: {extracted_data.gstin}) "
                            f"to {extracted_data.buyer_name} (GSTIN: {buyer_gstin_display}), "
                            f"with a total value of ₹{extracted_data.total_gross_worth:.2f}. "
                            f"Taxes applied - CGST: ₹{cgst:.2f}, SGST: ₹{sgst:.2f}, IGST: ₹{igst:.2f}. "
                            f"Place of supply: {pos}. Expense: {extracted_data.expense_ledger or 'N/A'}. "
                            f"TDS: {extracted_data.tds or 'N/A'}."
                        )
                        st.session_state.summary_rows.append({
                            "File Name": current_file_name, 
                            "Invoice Number": extracted_data.invoice_number,
                            "Date": extracted_data.date,
                            "Seller Name": extracted_data.seller_name,
                            "Seller GSTIN": extracted_data.gstin,
                            "Buyer Name": extracted_data.buyer_name,
                            "Buyer GSTIN": buyer_gstin_display,
                            "Total Gross Worth": extracted_data.total_gross_worth,
                            "CGST": cgst,
                            "SGST": sgst,
                            "IGST": igst,
                            "Place of Supply": pos,
                            "Expense Ledger": extracted_data.expense_ledger,
                            "TDS": extracted_data.tds,
                            "Narration": narration,
                        })
                    else:
                        # This case handles when extract_structured_data returned None (e.g. if it caught an error and didn't re-raise)
                        # However, the current extract_structured_data re-raises exceptions.
                        # This block would be relevant if extract_structured_data returned None on some non-exceptional failures.
                        st.warning(f"⚠️ No data was extracted from **{current_file_name}**. The function returned None.")
                    
                    progress_bar.progress((i + 1) / total_files)

                st.markdown(f"---")
                if successful_extractions > 0 and successful_extractions == total_files:
                    st.success(f"All {total_files} invoices processed successfully!")
                    st.balloons()
                elif successful_extractions > 0:
                    st.info(f"Successfully processed {successful_extractions} out of {total_files} invoices.")
                    st.balloons() # Still celebrate partial success
                elif total_files > 0 :
                    st.warning("Processing complete, but no data was successfully extracted from any file.")
                else: # Should not happen if button is clicked with uploaded_files
                    st.info("No files were processed.")


            asyncio.run(main_processing_async())
            progress_bar.progress(1.0) # Ensure progress bar completes


if st.session_state.summary_rows:
    st.subheader("📊 Extracted Invoice Summary")
    df = pd.DataFrame(st.session_state.summary_rows)
    st.dataframe(df)

    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='InvoiceSummary')
    excel_data = output_excel.getvalue()

    st.download_button(
        label="📥 Download Summary as Excel",
        data=excel_data,
        file_name="invoice_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
elif not uploaded_files and st.session_state.get('client') is not None : # Check if processing was attempted
    # This message appears if processing happened but summary_rows is empty
    st.info("No data was extracted from the processed files, or no files were uploaded for processing.")
elif not uploaded_files: # Initial state before any processing
     st.info("Upload PDF files and click 'Process Invoices' to see results.")
