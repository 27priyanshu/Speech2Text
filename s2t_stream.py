import streamlit as st
import speech_recognition as sr
from googletrans import Translator
from io import BytesIO

def hindi_voice_to_english_text(audio_file=None):
    # Initialize recognizer and translator
    recognizer = sr.Recognizer()
    translator = Translator()

    try:
        if audio_file:
            # Use uploaded audio file for transcription
            audio_data = sr.AudioFile(audio_file)
            with audio_data as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.record(source)
        else:
            # Use the microphone for input
            with sr.Microphone() as source:
                st.write("Speak something in Hindi...")
                # Adjust for ambient noise and record audio
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)

        # Recognize speech using Google Speech Recognition for Hindi
        st.write("Recognizing speech...")
        hindi_text = recognizer.recognize_google(audio, language='hi-IN')
        st.write(f"Transcribed Hindi Text: {hindi_text}")

        # Translate the transcribed Hindi text to English
        st.write("Translating to English...")
        translated_text = translator.translate(hindi_text, src='hi', dest='en')
        st.write(f"Translated English Text: {translated_text.text}")

        return hindi_text, translated_text.text

    except sr.UnknownValueError:
        st.error("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        st.error(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        st.error(f"Error during translation: {e}")

# Streamlit UI
st.title("Hindi Voice to English Text Transcription")

# Option to either upload an audio file or use microphone
option = st.radio("Choose input method", ("Microphone", "Upload Audio File"))

if option == "Microphone":
    if st.button("Record using Microphone"):
        hindi_voice_to_english_text()

elif option == "Upload Audio File":
    audio_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "ogg"])
    if audio_file is not None:
        # Converting the uploaded file to BytesIO for SpeechRecognition
        audio_bytes = BytesIO(audio_file.read())
        hindi_voice_to_english_text(audio_bytes)
