import speech_recognition as sr
from googletrans import Translator

def hindi_voice_to_english_text():
    # Initialize recognizer and translator
    recognizer = sr.Recognizer()
    translator = Translator()

    # Use the microphone for input
    with sr.Microphone() as source:
        print("Speak something in Hindi...")
        
        # Adjust for ambient noise and record audio
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

        try:
            # Recognize speech using Google Speech Recognition for Hindi
            print("Recognizing speech...")
            hindi_text = recognizer.recognize_google(audio, language='hi-IN')
            print(f"Transcribed Hindi Text: {hindi_text}")
            
            # Translate the transcribed Hindi text to English
            print("Translating to English...")
            translated_text = translator.translate(hindi_text, src='hi', dest='en')
            print(f"Translated English Text: {translated_text.text}")
            
            return translated_text.text

        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
        except Exception as e:
            print(f"Error during translation: {e}")

# Run the function
if __name__ == "__main__":
    hindi_voice_to_english_text()
