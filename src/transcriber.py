import asyncio
import assemblyai
import websockets
import pyaudio
import requests
import sys

# ToDO: Speaker Diaretization: Apparently not possible yet :(
# ToDO: Multi language: AssamblyAI supports only english for now :(

class Transcriber:

    def __init__(self, config):
        self.api_key = config['assemblyai']['api_key']
        #assemblyai.api_key = self.api_key
        assemblyai.settings.api_key = self.api_key
        # self.client = assemblyai.Client

        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 512 # 1024 was the default but recieved overflow

        self.websocket_url = config['websocket']['url']
        self.global_conversation = ""
        self.processor = None


        self.conversation_file = 'conversation.log'
        self.last_length = 0

        self.client = assemblyai.RealtimeTranscriber(
            sample_rate=16_000,
            on_data=self.on_data,
            on_error=self.on_error,
            on_open=self.on_open,
            on_close=self.on_close,
            end_utterance_silence_threshold=2000
        )

        self.client.connect()

    def start(self):
        # Test of processor
        # gpt_response = self.processor.process_transcription("can you tell me your experience with AWS?")
        # print(gpt_response)
        # return

        microphone_stream = assemblyai.extras.MicrophoneStream(sample_rate=16_000)
        self.client.stream(microphone_stream)
        self.client.close()

    def on_open(self, session_opened: assemblyai.RealtimeSessionOpened):
        # print("Session ID:", session_opened.session_id)
        print ("session_opened:", session_opened)


    def on_data(self, transcript: assemblyai.RealtimeTranscript):
        if not transcript.text:
            return

        if isinstance(transcript, assemblyai.RealtimeFinalTranscript):
            # full transcript.
            self.global_conversation += transcript.text + "\r\n"
            print(transcript.text, end="\r\n\r\n")
            self.save_transcript_to_file(transcript.text)

            # print("Confidence: ", transcript.confidence)
            self.query_processor()
            print("\r\n-------------------------------------------------\r\n")
        elif isinstance(transcript, assemblyai.RealtimePartialTranscript):
            self.print_dynamic(transcript.text)
        else:
            print(" -- Other --")
            print(transcript.text, end="\r")

    def on_error(self, error: assemblyai.RealtimeError):
        print("An error occured:", error)


    def on_close(self):
        print("Closing Session")

    def query_processor(self):
        if self.processor:
            # Llamar a GPT usando el prompt configurado y la conversación global acumulada
            gpt_response = self.processor.process_transcription(self.global_conversation)
            print(gpt_response)

    def print_dynamic(self, text):
        """Sobrescribe la línea anterior y borra el contenido residual."""
        # Agregar suficientes espacios para borrar el texto anterior si es más largo
        padding = ' ' * max(self.last_length - len(text), 0)
        sys.stdout.write('\r' + text + padding)
        sys.stdout.flush()
        self.last_length = len(text)  # Actualiza la longitud del texto actual


    def save_transcript_to_file(self, text):
        """Guarda la transcripción final en el archivo."""
        try:
            with open(self.conversation_file, 'a') as f:  # Abrir el archivo en modo 'append'
                f.write(text + "\n")
        except Exception as e:
            print(f"Error guardando la transcripción: {e}")
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

