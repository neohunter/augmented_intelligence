import asyncio
import assemblyai
import websockets
import pyaudio
import requests
import sys
import shutil
import time
import os
import re

# TODO: Speaker Diarization: Apparently not supported yet :(
# TODO: Multi-language: AssemblyAI only supports English for now :(
# TODO: Save to file with the name format: YYYY-MM-DD_main_topic.log

class Transcriber:

    def __init__(self, config):
        self.config = config
        self.api_key = config['assemblyai']['api_key']
        assemblyai.settings.api_key = self.api_key

        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 512  # 1024 caused input overflow

        self.websocket_url = config['websocket']['url']
        self.global_conversation = ""
        self.processor = None
        self.start_time = None  # Timestamp when the conversation starts

        self.current_topic = None  # Store the conversation's topic
        self.temp_file = None  # Store the temporary filename
        self.conversation_file = None  # Store the final filename

        self.last_length = 0
        self.last_lines_used = 0  # Track how many lines the last partial transcript used
        self.last_start_time_transcript = ""  # To store the starting point of the last section

        self.client = assemblyai.RealtimeTranscriber(
            sample_rate=16_000,
            on_data=self.on_data,
            on_error=self.on_error,
            on_open=self.on_open,
            on_close=self.on_close,
            end_utterance_silence_threshold=2000
        )

        self.client.connect()

        print("\r\n")

    def start(self):
        # Test of processor
        # gpt_response = self.processor.process_transcription("can you tell me your experience with AWS?")
        # print(gpt_response)
        # return

        microphone_stream = assemblyai.extras.MicrophoneStream(sample_rate=16_000)
        self.client.stream(microphone_stream)
        self.client.close()

    def on_open(self, session_opened: assemblyai.RealtimeSessionOpened):
        """Called when the transcription session starts."""
        self.start_time = time.time()
        date_str = time.strftime("%Y-%m-%d")
        self.temp_file = f"transcripts/{date_str}_temp.log"

    def on_data(self, transcript: assemblyai.RealtimeTranscript):
        """Handles real-time transcript data."""
        if not transcript.text:
            return

        current_time = time.time()  # Current time
        elapsed_time = current_time - self.start_time  # Time since the session started
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        time_formatted = f"({minutes:02}:{seconds:02})"

        text_to_print = f"{time_formatted} {transcript.text}\r"

        if isinstance(transcript, assemblyai.RealtimeFinalTranscript):
            # Final transcript
            self.clear_last_lines(self.last_lines_used)
            self.last_lines_used = 0

            self.global_conversation += text_to_print + "\r\n"
            print(text_to_print, end="\r\n")
            self.save_transcript_to_file(text_to_print)

            # print("Confidence: ", transcript.confidence)
            self.query_processor()
            # print("\r\n-------------------------------------------------\r\n")
        elif isinstance(transcript, assemblyai.RealtimePartialTranscript):
            # Partial transcript
            self.clear_last_lines(self.last_lines_used)
            terminal_width = self.get_terminal_width()
            self.last_lines_used = self.calculate_lines(text_to_print, terminal_width)

            sys.stdout.write(text_to_print)

        else:
            print(" -- Other --")
            print(transcript.text, end="\r")

    def on_error(self, error: assemblyai.RealtimeError):
        """Handles errors that occur during transcription."""
        print("An error occurred:", error)

    def on_close(self):
        """Called when the transcription session ends."""
        print("Closing Session")

    def query_processor(self):
        """Processes the accumulated conversation using GPT and updates the current section."""
        if self.processor:
            # Get the transcript since the last section's start time
            transcript_since_last_section = self.get_transcript_since_last_start_time()

            # Call GPT with only the relevant portion of the transcript
            gpt_response = self.processor.process_transcription(transcript_since_last_section)
            print(gpt_response + "\r\n\r\n")

            # Extract and format the current topic from the GPT response
            if not self.current_topic:
                topic = self.extract_and_format_topic(gpt_response)
                if topic:
                    print(f"Identified Topic: {topic}")
                    self.update_topic(topic)

            # WIP attempt to receive response as json to create a UI.
            # Update the current section with the new GPT data (concepts, questions, etc.)
            if self.config['general_settings']['use_json_response']:
                self.update_current_section(gpt_response)


    def get_transcript_since_last_start_time(self):
        """Return the transcript text from the last section's start time."""
        if not self.start_time:
            # If no start time, return the full conversation
            return self.global_conversation
        else:
            # Get the transcript since the last section's start time
            last_start_time_pos = self.global_conversation.find(self.last_start_time_transcript)
            return self.global_conversation[last_start_time_pos:]

    def update_current_section(self, gpt_response):
        """Update the current section with the latest GPT response data."""
        # Parse GPT response for key concepts, questions, etc.
        section_data = self.parse_gpt_response(gpt_response)

        # Update the current section of the conversation
        self.conversation["current_section"].update({
            "topic": section_data.get("topic", ""),
            "transcript": self.get_transcript_since_last_start_time(),
            "key_concepts": section_data.get("key_concepts", []),
            "questions": section_data.get("questions", []),
            "follow_up_questions": section_data.get("follow_up_questions", []),
            "keywords": section_data.get("keywords", [])
        })


    def complete_current_section(self):
        """Move the current section to previous_sections and start a new section."""
        # Mark the end time of the current section
        self.conversation["current_section"]["end_time"] = self.get_current_time()

        # Move the current section to previous_sections
        self.conversation["previous_sections"].append(self.conversation["current_section"])

        # Start a new section
        self.conversation["current_section"] = {
            "section_id": len(self.conversation["previous_sections"]) + 1,
            "topic": "",
            "transcript": "",
            "start_time": self.get_current_time(),
            "end_time": None,
            "key_concepts": [],
            "questions": [],
            "follow_up_questions": [],
            "keywords": []
        }

    def clear_last_lines(self, lines_to_clear):
        """Clears the last printed lines in the terminal."""
        if lines_to_clear <= 1:
            return

        for _ in range(lines_to_clear - 1):
            sys.stdout.write('\033[F')  # Move the cursor up
        sys.stdout.flush()

    def get_terminal_width(self):
        """Returns the width of the terminal."""
        size = shutil.get_terminal_size()
        return size.columns

    def calculate_lines(self, text, terminal_width):
        """Calculates the number of lines the text would occupy in the terminal."""
        return (len(text) // terminal_width) + 1

    def save_transcript_to_file(self, text):
        """Saves the current transcript to the file."""
        filename = self.conversation_file if self.conversation_file else self.temp_file

        try:
            with open(filename, 'a') as f:
                f.write(text + "\n")
        except Exception as e:
            print(f"Error saving the transcript: {e}")

    # ToDO move this to processor
    def update_topic(self, new_topic):
        """Updates the conversation topic and renames the log file."""
        self.current_topic = new_topic
        # Update the last_start_time_transcript to start tracking from this point onward
        self.last_start_time_transcript = self.global_conversation

        date_str = time.strftime("%Y-%m-%d")
        new_filename = f"transcripts/{date_str}_{self.current_topic}.log"
        os.rename(self.temp_file, new_filename)
        self.conversation_file = new_filename
        print(f"File renamed to {self.conversation_file}")

    def extract_and_format_topic(self, gpt_response):
        """
        Extracts the topic from the GPT response, formats it by converting to lowercase,
        replacing spaces with underscores, and removing unwanted characters.
        """
        lines = gpt_response.splitlines()

        for line in lines:
            if line.startswith("Topic:"):
                topic = line[len("Topic:"):].strip()
                formatted_topic = re.sub(r'[^a-z_]', '', topic.lower().replace(' ', '_'))
                return formatted_topic

        return None  # Return None if no topic is found


    # def transcribe(self, audio_stream=None, use_microphone=True):
    #     if use_microphone:
    #         return self.transcribe_from_mic()
    #     else:
    #         return self.transcribe_from_stream(audio_stream)

    # def transcribe_from_mic(self):
    #     p = pyaudio.PyAudio()
    #     stream = p.open(format=self.audio_format,
    #                     channels=self.channels,
    #                     rate=self.rate,
    #                     input=True,
    #                     frames_per_buffer=self.chunk)

    #     print("Grabando desde el micrófono...")
    #     frames = []

    #     try:
    #         while True:
    #             data = stream.read(self.chunk)
    #             frames.append(data)

    #             response = self.client.transcribe(b''.join(frames), real_time=True)
    #             print(f"Transcripción parcial: {response}")
    #     except KeyboardInterrupt:
    #         print("Interrupción de la grabación.")

    #     stream.stop_stream()
    #     stream.close()
    #     p.terminate()

    # def transcribe_from_stream(self, stream_url):
    #     print(f"Transcribiendo desde stream de audio: {stream_url}")
    #     response = requests.get(stream_url, stream=True)
    #     for chunk in response.iter_content(chunk_size=1024):
    #         if chunk:
    #             transcription = self.client.transcribe(chunk, real_time=True)
    #             print(f"Transcripción parcial desde stream: {transcription}")

    # async def transcribe_ws(self):
    #     async with websockets.connect(self.websocket_url, extra_headers={'Authorization': self.api_key}) as websocket:
    #         while True:
    #             try:
    #                 result = await websocket.recv()
    #                 yield result.get('text', '')
    #             except websockets.ConnectionClosedError:
    #                 break
    #             except Exception as e:
    #                 print(f"Error: {e}")

