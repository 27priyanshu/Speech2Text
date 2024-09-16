import streamlit as st
import speech_recognition as sr
from googletrans import Translator
from io import BytesIO

# Function to process the transcription and translation
def hindi_voice_to_english_text(audio_data):
    recognizer = sr.Recognizer()
    translator = Translator()
    hindi_text = ""  # Store the full transcribed text

    try:
        # Process audio in chunks
        with audio_data as source:
            recognizer.adjust_for_ambient_noise(source)
            while True:
                try:
                    # Record audio in chunks (e.g., 60 seconds per chunk)
                    audio_chunk = recognizer.record(source, duration=60)
                    chunk_text = recognizer.recognize_google(audio_chunk, language='hi-IN')
                    hindi_text += chunk_text + " "  # Append each chunk to the full text
                    st.write(f"Transcribed Chunk: {chunk_text}")
                except sr.WaitTimeoutError:
                    break  # No more audio to process
                except sr.UnknownValueError:
                    st.error("Could not understand the audio")
                    break

        if hindi_text.strip() == "":
            st.error("No valid Hindi text transcribed. Skipping translation.")
            return None, None
        
        # Translate the full transcribed Hindi text to English
        st.write("Translating to English...")
        translated_text = translator.translate(hindi_text, src='hi', dest='en')
        st.write(f"Translated English Text: {translated_text.text}")

        return hindi_text, translated_text.text

    except sr.RequestError as e:
        st.error(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        st.error(f"Error during translation: {e}")

# Streamlit UI
st.title("Hindi Voice to English Text Transcription")

# Option to either upload an audio file or use microphone
option = st.radio("Choose input method", ("Microphone", "Upload Audio File"))

# State for recording status
if "recording" not in st.session_state:
    st.session_state["recording"] = False
if "processing" not in st.session_state:
    st.session_state["processing"] = False

def start_recording():
    st.session_state["recording"] = True

def stop_recording():
    st.session_state["recording"] = False
    st.session_state["processing"] = True

if option == "Microphone":
    if not st.session_state["recording"]:
        if st.button("Start Recording using Microphone"):
            start_recording()

    if st.session_state["recording"]:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.write("Recording... Speak something in Hindi.")
            recognizer.adjust_for_ambient_noise(source)

            # Streamlit allows async-like buttons to stop the recording
            stop_btn = st.button("Stop Recording")
            if stop_btn:
                # Record the audio and store it in a file-like object (BytesIO)
                audio = recognizer.listen(source, timeout=300, phrase_time_limit=300)  # Recording up to 5 minutes or until stopped
                audio_data = BytesIO(audio.get_wav_data())  # Convert to a file-like object
                stop_recording()

    if st.session_state["processing"]:
        st.write("Wait... Processing the recording...")
        st.write("Recognizing speech...")
        hindi_voice_to_english_text(sr.AudioFile(audio_data))  # Use sr.AudioFile to handle file-like object
        st.session_state["processing"] = False  # Reset processing state after completion

elif option == "Upload Audio File":
    audio_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "ogg"])
    if audio_file is not None:
        # Converting the uploaded file to a file-like object for SpeechRecognition
        audio_bytes = BytesIO(audio_file.read())
        audio_data = sr.AudioFile(audio_bytes)  # Convert to a file-like object compatible with recognizer
        st.write("Wait... Processing the uploaded file...")
        st.write("Recognizing speech...")
        hindi_voice_to_english_text(audio_data)
