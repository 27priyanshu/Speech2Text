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

# Configure Google Gemini API
genai.configure(api_key="AIzaSyAOYCODmo6n5A75oWBiAAMscPISpKhel3Y")  # Replace with your actual API key

# Function to structure the transcription using Gemini
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
        
        # Parse the response to get the structured data
        response_text = response.text.strip()
        # Remove any markdown formatting if present
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
        # Hindi speech transcription
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

# Process audio for transcription and structuring
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

        # Structure the transcription using Gemini
        structured_result = structure_transcription_with_gemini(english_text)
        st.write("Structured Transcription:")
        if "error" in structured_result:
            st.error(f"Error: {structured_result['error']}")
            if "raw_response" in structured_result:
                st.write("Raw API Response:")
                st.code(structured_result['raw_response'])
        else:
            st.json(structured_result)
    except Exception as e:
        st.error(f"Error processing audio: {str(e)}")
    finally:
        if 'temp_audio_path' in locals():
            os.unlink(temp_audio_path)

# Streamlit UI
def main():
    st.title("Hindi Voice to English Text Transcription")

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
            try:
                process_audio(audio_file)
            except Exception as e:
                st.error(f"Error processing uploaded file: {str(e)}")

if __name__ == "__main__":
    main()