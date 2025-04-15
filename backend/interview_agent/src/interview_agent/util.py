# Initialize OpenAI client
import io
import threading
from elevenlabs import ElevenLabs, VoiceSettings, play
from langchain_openai import OpenAI
from scipy.io.wavfile import write
import sounddevice as sd
import numpy as np
import os

# from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
from state import State

openai_client = OpenAI()

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVEN_LABS_API_KEY"))


def record_audio_until_stop(state: State):
    """Records audio from the microphone until Enter is pressed, then saves it to a .wav file."""

    audio_data = []  # List to store audio chunks
    recording = True  # Flag to control recording
    sample_rate = 16000  # (kHz) Adequate for human voice frequency

    def record_audio():
        """Continuously records audio until the recording flag is set to False."""
        nonlocal audio_data, recording
        with sd.InputStream(
            samplerate=sample_rate, channels=1, dtype="int16"
        ) as stream:
            print("Recording your instruction! ... Press Enter to stop recording.")
            while recording:
                audio_chunk, _ = stream.read(1024)  # Read audio data in chunks
                audio_data.append(audio_chunk)

    def stop_recording():
        """Waits for user input to stop the recording."""
        input()  # Wait for Enter key press
        nonlocal recording
        recording = False

    # Start recording in a separate thread
    recording_thread = threading.Thread(target=record_audio)
    recording_thread.start()

    # Start a thread to listen for the Enter key
    stop_thread = threading.Thread(target=stop_recording)
    stop_thread.start()

    # Wait for both threads to complete
    stop_thread.join()
    recording_thread.join()

    # Stack all audio chunks into a single NumPy array and write to file
    audio_data = np.concatenate(audio_data, axis=0)

    # Convert to WAV format in-memory
    audio_bytes = io.BytesIO()
    write(
        audio_bytes, sample_rate, audio_data
    )  # Use scipy's write function to save to BytesIO
    audio_bytes.seek(0)  # Go to the start of the BytesIO buffer
    audio_bytes.name = "audio.wav"  # Set a filename for the in-memory file

    # Transcribe via Whisper
    transcription = openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_bytes,
    )

    # Print the transcription
    print("Here is the transcription:", transcription.text)

    # Write to messages
    current_qa = state["qa_list"][len(state["completed_qa"])]
    return {"messages": [HumanMessage(content=transcription.text)]}


def play_audio(state: State):
    """Plays the audio response from the remote graph with ElevenLabs."""

    # Response from the agent
    response = state["qa_list"][-1].question
    print("Response:", response)

    # Prepare text by replacing ** with empty strings
    # These can cause unexpected behavior in ElevenLabs
    cleaned_text = response.replace("**", "")

    # Call text_to_speech API with turbo model for low latency
    response = elevenlabs_client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",  # Adam pre-made voice
        output_format="mp3_22050_32",
        text=cleaned_text,
        model_id="eleven_turbo_v2_5",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # Play the audio back
    play(response)
