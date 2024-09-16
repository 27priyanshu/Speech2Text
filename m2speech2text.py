import speech_recognition as sr
from googletrans import Translator
from fastapi import FastAPI, UploadFile, File
import uvicorn
from pydub import AudioSegment
import io

app = FastAPI()

@app.post("/translate/")
async def translate_audio(file: UploadFile = File(...)):
    recognizer = sr.Recognizer()
    translator = Translator()
    
    # Read the uploaded audio file
    audio_data = await file.read()
    
    # Check if the file is .m4a and convert to .wav using pydub
    if file.filename.endswith('.m4a'):
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="m4a")
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)
    else:
        wav_io = io.BytesIO(audio_data)

    # Use AudioFile from speech_recognition to handle the .wav input
    with sr.AudioFile(wav_io) as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.record(source)

        try:
            # Recognize speech from the audio
            hindi_text = recognizer.recognize_google(audio, language='hi-IN')
            print(f"Transcribed Hindi Text: {hindi_text}")
            
            # Translate to English
            translated_text = translator.translate(hindi_text, src='hi', dest='en').text
            print(f"Translated English Text: {translated_text}")
            
            return {"hindi_text": hindi_text, "translated_text": translated_text}

        except sr.UnknownValueError:
            return {"error": "Speech Recognition could not understand audio"}
        except sr.RequestError as e:
            return {"error": f"Speech Recognition request failed: {e}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
