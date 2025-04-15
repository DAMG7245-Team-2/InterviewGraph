from __future__ import annotations
from typing import Literal
import io
import threading
from elevenlabs import ElevenLabs, VoiceSettings, play
from openai import OpenAI
from scipy.io.wavfile import write
import sounddevice as sd
import numpy as np
import os
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from typing import TypedDict, List, Annotated
import operator
from pydantic import BaseModel, Field
from IPython.display import Image, display
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, Send, interrupt
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from interview_agent.state import *

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
        language="en",
        file=audio_bytes,
    )
    current_qa = state["qa_list"][len(state["completed_qa"])]
    current_qa.given_answer = transcription.text
    # Update the last QA object with the user's answer
    state["qa_list"][len(state["completed_qa"])] = current_qa
    # Print the transcription
    print("Here is the transcription:", transcription.text)

    # Write to messages
    return {"completed_qa": [current_qa]}


def play_audio(state: State):
    """Plays the audio response from the remote graph with ElevenLabs."""

    # Response from the agent
    response = state["qa_list"][len(state["completed_qa"])].question
    print("Response:", response)

    # Prepare text by replacing ** with empty strings
    # These can cause unexpected behavior in ElevenLabs
    cleaned_text = response.replace("**", "")

    # Call text_to_speech API with turbo model for low latency
    response = elevenlabs_client.text_to_speech.convert(
        voice_id="UgBBYS2sOqTuMpoF3BR0",  # Adam pre-made voice
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


def generate_question(state: State):
    """Generate a question based on the context provided."""
    # Initialize the chat model
    chat_model = init_chat_model(model_provider="openai", model="gpt-4o-mini")

    chat_model_with_structured_output = chat_model.with_structured_output(QAList)

    # Create a system message with the context
    system_message = SystemMessage(
        content=f"You are an expert technical quizmaster, your task is to generate at least 2 quiz questions QAList using the context provided to you: \n\n{str(context)}\n\n. Each QA should have question, expected_answer fields."
    )

    # Create a human message to ask for a question
    human_message = HumanMessage(
        content="Please generate a question based on the provided context."
    )

    # Send the messages to the chat model and get the response
    response = chat_model_with_structured_output.invoke([system_message, human_message])
    # print("generate question llm response", response)
    # Extract the generated question from the response
    generated_qa_list = response.qa_list
    # print("generated_qa_list", generated_qa_list)
    return {"qa_list": generated_qa_list}


async def human_node(state: State):
    """Human node to get the answer from the user."""
    # Display the question and context
    # print(f"Question: {state['qa_list'][-1].question}")
    # print(f"Context: {context}")

    # Get the answer from the user
    current_qa = state["qa_list"][len(state["completed_qa"])]
    print(f"Question no: {len(state['completed_qa'])} of {len(state['qa_list'])}")
    user_answer = interrupt(
        f"Question: {current_qa.question} \n Please provide your answer:"
    )

    # Update the last QA object with the user's answer
    current_qa.given_answer = user_answer

    # return {"completed_qa": [state['qa_list'][-1]]}
    # if len(state['completed_qa']) == len(state['qa_list'])-1:
    # return Command(update={"completed_qa": [current_qa]}, goto="generate_feedback")
    # else:
    #     return Command(update={"completed_qa": [current_qa]}, goto="human_node")
    return {"completed_qa": [current_qa]}


def generate_feedback(state: State):
    """Generate feedback based on the answer provided by the user."""
    # Initialize the chat model
    chat_model = init_chat_model(model_provider="openai", model="gpt-4o-mini")

    chat_model_with_structured_output = chat_model.with_structured_output(Feedback)

    responses = []
    for qa in state["completed_qa"]:
        # Calculate the similarity score (this is a placeholder, you should replace it with actual similarity calculation)
        # Create a system message with the context
        system_message = SystemMessage(
            content=f'You are an expert technical quizzer, You are given the question, expected_answer, given_answer: \n\n{qa}\n\n. Based on this information, generate feedback for the user. The feedback should include a similarity score between the expected answer and the given answer, and a brief explanation of the score. The feedback should be in the format: \n\n{{"similarity": <similarity_score>, "feedback": <feedback>}}'
        )

        # Create a human message to ask for feedback
        human_message = HumanMessage(
            content="Please generate feedback based on the provided context."
        )

        # Send the messages to the chat model and get the response
        response = chat_model_with_structured_output.invoke(
            [system_message, human_message]
        )
        print("feedback llm response", response)
        responses.append(response)

    return {"feedback": [responses]}


def route(state: State) -> Literal["audio_output", "feedback_node"]:
    if len(state["qa_list"]) == len(state["completed_qa"]):
        return "feedback_node"
    else:
        return "audio_output"


poc_workflow = StateGraph(State, input=InputState)
poc_workflow.add_node("generate_question", generate_question)
# poc_workflow.add_node("human_node",human_node)
poc_workflow.add_node("audio_output", play_audio)
poc_workflow.add_node("audio_input", record_audio_until_stop)
poc_workflow.add_node("feedback_node", generate_feedback)

poc_workflow.add_edge(START, "generate_question")
poc_workflow.add_edge("generate_question", "audio_output")
# poc_workflow.add_edge("human_node","audio_output")
poc_workflow.add_edge("audio_output", "audio_input")
poc_workflow.add_conditional_edges("audio_input", route)
poc_workflow.add_edge("feedback_node", END)

checkpointer = MemorySaver()
graph = poc_workflow.compile()
