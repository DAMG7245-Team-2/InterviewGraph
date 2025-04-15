# Initialize OpenAI client

# from langgraph.graph import MessagesState

# from state import State

# openai_client = OpenAI()

# # Initialize ElevenLabs client
# elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVEN_LABS_API_KEY"))


# def record_audio_until_stop(state: State):
#     """Records audio from the microphone until Enter is pressed, then saves it to a .wav file."""

#     audio_data = []  # List to store audio chunks
#     recording = True  # Flag to control recording
#     sample_rate = 16000  # (kHz) Adequate for human voice frequency

#     def record_audio():
#         """Continuously records audio until the recording flag is set to False."""
#         nonlocal audio_data, recording
#         with sd.InputStream(
#             samplerate=sample_rate, channels=1, dtype="int16"
#         ) as stream:
#             print("Recording your instruction! ... Press Enter to stop recording.")
#             while recording:
#                 audio_chunk, _ = stream.read(1024)  # Read audio data in chunks
#                 audio_data.append(audio_chunk)

#     def stop_recording():
#         """Waits for user input to stop the recording."""
#         input()  # Wait for Enter key press
#         nonlocal recording
#         recording = False

#     # Start recording in a separate thread
#     recording_thread = threading.Thread(target=record_audio)
#     recording_thread.start()

#     # Start a thread to listen for the Enter key
#     stop_thread = threading.Thread(target=stop_recording)
#     stop_thread.start()

#     # Wait for both threads to complete
#     stop_thread.join()
#     recording_thread.join()

#     # Stack all audio chunks into a single NumPy array and write to file
#     audio_data = np.concatenate(audio_data, axis=0)

#     # Convert to WAV format in-memory
#     audio_bytes = io.BytesIO()
#     write(
#         audio_bytes, sample_rate, audio_data
#     )  # Use scipy's write function to save to BytesIO
#     audio_bytes.seek(0)  # Go to the start of the BytesIO buffer
#     audio_bytes.name = "audio.wav"  # Set a filename for the in-memory file

#     # Transcribe via Whisper
#     transcription = openai_client.audio.transcriptions.create(
#         model="whisper-1",
#         file=audio_bytes,
#     )

#     # Print the transcription
#     print("Here is the transcription:", transcription.text)

#     # Write to messages
#     current_qa = state["qa_list"][len(state["completed_qa"])]
#     return {"messages": [HumanMessage(content=transcription.text)]}


# def play_audio(state: State):
#     """Plays the audio response from the remote graph with ElevenLabs."""

#     # Response from the agent
#     response = state["qa_list"][-1].question
#     print("Response:", response)

#     # Prepare text by replacing ** with empty strings
#     # These can cause unexpected behavior in ElevenLabs
#     cleaned_text = response.replace("**", "")

#     # Call text_to_speech API with turbo model for low latency
#     response = elevenlabs_client.text_to_speech.convert(
#         voice_id="pNInz6obpgDQGcFmaJgB",  # Adam pre-made voice
#         output_format="mp3_22050_32",
#         text=cleaned_text,
#         model_id="eleven_turbo_v2_5",
#         voice_settings=VoiceSettings(
#             stability=0.0,
#             similarity_boost=1.0,
#             style=0.0,
#             use_speaker_boost=True,
#         ),
#     )

#     # Play the audio back
#     play(response)


def get_context():
    context = [
        """What is a Unix shell? Is Bash the only Unix shell?
A Unix shell is a software that provides a user interface for the underlying operating system. Unix shells typically provide a textual user interface - a command line interpreter - that may be used for entering and running commands, or create scripts that run a series of commands and can be used to express more advanced behavior.

Bash is not the only Unix shell, but just one of many. Short for Bourne-Again Shell, it is also one of the many Bourne-compatible shells. However, Bash is arguably one of the most popular shells around. There are other, modern shells available that often retain backwards compatibility with Bash but provide more functionality and features, such as the Z Shell (zsh).""",
        """What are shared, slave, private, and unbindable mountpoints?
A mount point that is shared may be replicated as many times as needed, and each copy will continue to be the exact same. Other mount points that appear under a shared mount point in some subdirectory will appear in all the other replicated mount points as it is.

A slave mount point is similar to a shared mount point with the small exception that the “sharing” of mount point information happens in one direction. A mount point that is slave will only receive mount and unmount events. Anything that is mounted under this replicated mount point will not move towards the original mount point.

A private mount point is exactly what the name implies: private. Mount points that appear under a private mount point will not be shown elsewhere in the other replicated mount points unless they are explicitly mounted there as well.

An unbindable mount point, which by definition is also private, cannot be replicated elsewhere through the use of the bind flag of the mount system call or command.""",
        """What is a swap space?
Swap space is a certain amount of space used by Linux to temporarily hold some programs that are running concurrently. This happens when RAM does not have enough memory to hold all programs that are executing.""",
    ]
    return context
