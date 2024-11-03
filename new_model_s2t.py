import streamlit as st
import speech_recognition as sr
from googletrans import Translator
import io
import os
import json
from datetime import datetime
import tempfile
import soundfile as sf
import google.generativeai as genai
import pandas as pd
import pyodbc
from config.config import API_KEY  # Import API_KEY from config file
from config.config import get_db_connection  # Import database connection function

# Configure Google Gemini API with key from config
genai.configure(api_key=API_KEY)

# Function to structure transcription using Gemini
def structure_transcription_with_gemini(text):
    try:
        current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        prompt = f"""
        Given the following transcribed text, extract and structure the information into the following JSON format:
        {{
            "Date": "{current_datetime}",
            "Name": "Full Name",
            "Emp code": "Employee Code",
            "Work Done": "Description of work done"
        }}

        Transcribed text:
        {text}

        Use the provided date and time. If any other information is missing, use "Not Available" as the value.
        Ensure the response is a valid JSON object.
        """

        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1].strip()
        
        structured_data = json.loads(response_text)
        return structured_data
    except json.JSONDecodeError as e:
        return {"error": f"JSON parsing error: {str(e)}", "raw_response": response_text}
    except Exception as e:
        return {"error": f"Error structuring transcription with Gemini: {str(e)}"}

# Transcription function (Hindi recognition)
def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language='hi-IN')
        return text
    except sr.UnknownValueError:
        return "Speech recognition could not understand audio"
    except sr.RequestError as e:
        return f"Could not request results from Google Speech Recognition service; {e}"

# Translation function (Hindi to English)
def translate_text(text, target_language="en"):
    translator = Translator()
    try:
        result = translator.translate(text, src='hi', dest=target_language)
        return result.text
    except Exception as e:
        return f"Translation error: {str(e)}"

# Save transcription data to SQL Server
def save_transcription_to_db(structured_data, hindi_text, english_text):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transcriptions (date, name, emp_code, work_done, hindi_text, english_text)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (structured_data["Date"], structured_data["Name"], structured_data["Emp code"],
              structured_data["Work Done"], hindi_text, english_text))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False

# Process audio for transcription, structuring, and saving to database
def process_audio(audio_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_file.read())
            temp_audio_path = temp_audio.name

        hindi_text = transcribe_audio(temp_audio_path)
        st.write("Transcribed Hindi Text:")
        st.write(hindi_text)
        
        english_text = translate_text(hindi_text)
        st.write("Translated English Text:")
        st.write(english_text)

        structured_result = structure_transcription_with_gemini(english_text)
        st.write("Structured Transcription:")
        if "error" in structured_result:
            st.error(f"Error: {structured_result['error']}")
            if "raw_response" in structured_result:
                st.write("Raw API Response:")
                st.code(structured_result['raw_response'])
        else:
            st.json(structured_result)
            if save_transcription_to_db(structured_result, hindi_text, english_text):
                st.success("Transcription saved to database successfully!")
            else:
                st.error("Failed to save transcription to database.")
    except Exception as e:
        st.error(f"Error processing audio: {str(e)}")
    finally:
        if 'temp_audio_path' in locals():
            os.unlink(temp_audio_path)

# Download all transcriptions as Excel
def download_transcriptions_as_excel():
    try:
        conn = get_db_connection()
        query = "SELECT * FROM transcriptions"
        df = pd.read_sql(query, conn)
        conn.close()
        
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error downloading transcriptions: {str(e)}")
        return None

# View transcriptions function
def view_transcriptions():
    try:
        conn = get_db_connection()
        query = "SELECT * FROM transcriptions ORDER BY date DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            st.write("Recent Transcriptions:")
            st.dataframe(df)
        else:
            st.info("No transcriptions found in the database.")
    except Exception as e:
        st.error(f"Error viewing transcriptions: {str(e)}")

# Streamlit UI
def main():
    st.title("Hindi Voice to English Text Transcription")

    # Add tabs
    tab1, tab2 = st.tabs(["Record/Upload", "View Transcriptions"])

    with tab1:
        option = st.radio("Choose input method", ("Microphone", "Upload Audio File"))

        if option == "Microphone":
            if st.button("Record using Microphone"):
                try:
                    with st.spinner("Recording..."):
                        recognizer = sr.Recognizer()
                        with sr.Microphone() as source:
                            st.write("Speak something in Hindi...")
                            audio = recognizer.listen(source, timeout=5)
                    
                    audio_data = audio.get_wav_data()
                    with io.BytesIO(audio_data) as audio_file:
                        process_audio(audio_file)
                except Exception as e:
                    st.error(f"Error recording audio: {str(e)}")

        elif option == "Upload Audio File":
            audio_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "ogg"])
            if audio_file is not None:
                process_audio(audio_file)

        # Excel Download button
        if st.button("Download All Transcriptions as Excel"):
            buffer = download_transcriptions_as_excel()
            if buffer:
                st.download_button(
                    label="Download Excel File",
                    data=buffer,
                    file_name="transcriptions.xlsx",
                    mime="application/vnd.ms-excel"
                )

    with tab2:
        view_transcriptions()

if __name__ == "__main__":
    main()