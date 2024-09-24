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

# ToDO: Speaker Diaretization: Apparently not possible yet :(
# ToDO: Multi language: AssamblyAI supports only english for now :(
# ToDO: Save to file, set name to YYYY-MM-DD_main_topic.log

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
        self.start_time = None

        self.current_topic = None  # Almacenar el tema de la conversación
        self.temp_file = None  # Almacenar el nombre del archivo temporal
        self.conversation_file = None  # Almacenar el nombre del archivo final

        self.last_length = 0
        self.last_lines_used = 0  # Para almacenar cuántas líneas usó la última transcripción parcial

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
        # print("Session ID:", session_opened.session_id)
        # print ("session_opened:", session_opened)
        self.start_time = time.time()
        date_str = time.strftime("%Y-%m-%d")
        self.temp_file = f"transcripts/{date_str}_temp.log"


    def on_data(self, transcript: assemblyai.RealtimeTranscript):
        if not transcript.text:
            return

        current_time = time.time()  # Tiempo actual
        elapsed_time = current_time - self.start_time  # Tiempo transcurrido desde el inicio
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        time_formatted = f"({minutes:02}:{seconds:02})"

        text_to_print = f"{time_formatted} {transcript.text}\r"

        if isinstance(transcript, assemblyai.RealtimeFinalTranscript):
            # full transcript.
            self.clear_last_lines(self.last_lines_used)
            self.last_lines_used = 0

            self.global_conversation += text_to_print + "\r\n"
            print(text_to_print, end="\r\n")
            self.save_transcript_to_file(text_to_print)

            # print("Confidence: ", transcript.confidence)
            # self.query_processor()
            # print("\r\n-------------------------------------------------\r\n")
        elif isinstance(transcript, assemblyai.RealtimePartialTranscript):
            # Partial transcript
            # Borrar las líneas anteriores
            self.clear_last_lines(self.last_lines_used)

            # Calcular las nuevas líneas usadas
            terminal_width = self.get_terminal_width()

            self.last_lines_used = self.calculate_lines(text_to_print, terminal_width)

            # Imprimir la nueva transcripción parcial
            sys.stdout.write(text_to_print)
            # sys.stdout.flush()
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

            if not self.current_topic:

                topic = self.extract_and_format_topic(gpt_response)

                if topic:
                    print(f"Topic identificado: {topic}")
                    self.update_topic(topic)


    def clear_last_lines(self, lines_to_clear):
        """Borra las últimas líneas impresas."""
        if lines_to_clear <= 1:
            return

        terminal_width = self.get_terminal_width()
        padding = ' ' * (terminal_width - 1)

        for _ in range(lines_to_clear - 1):

            #sys.stdout.write('\r' + padding)
            # sys.stdout.write('\033[K')  # Borra la línea
            # Mover el cursor hacia arriba y borrar la línea actual
            sys.stdout.write('\033[F')  # Mueve hacia arriba


        # sys.stdout.flush()

    def get_terminal_width(self):
        size = shutil.get_terminal_size()
        return size.columns

    def calculate_lines(self, text, terminal_width):
        total_lines = 0
        # Calcular cuántas líneas se necesitan para imprimir el texto en función del ancho de la terminal
        total_lines += (len(text) // terminal_width) + 1
        return total_lines


    def print_dynamic(self, text):
        """Sobrescribe la línea anterior y borra el contenido residual."""
        # Agregar suficientes espacios para borrar el texto anterior si es más largo
        padding = ' ' * max(self.last_length - len(text), 0)
        sys.stdout.write('\r' + text + padding)
        # sys.stdout.flush()
        self.last_length = len(text)  # Actualiza la longitud del texto actual

    def update_topic(self, new_topic):
        """Actualizar el tema de la conversación y renombrar el archivo."""
        self.current_topic = new_topic
        date_str = time.strftime("%Y-%m-%d")
        # Renombrar el archivo temporal al nombre final con el tema
        new_filename = f"{date_str}_{self.current_topic}.log"
        os.rename(self.temp_file, new_filename)
        self.conversation_file = new_filename
        print(f"Archivo renombrado a {self.conversation_file}")


    def save_transcript_to_file(self, text):
        """Guarda la transcripción final en el archivo."""
        if not self.conversation_file:
            filename = self.temp_file
        else:
            filename = self.conversation_file

        try:
            with open(filename, 'a') as f:  # Abrir el archivo en modo 'append'
                f.write(text + "\n")
        except Exception as e:
            print(f"Error guardando la transcripción: {e}")

    def extract_and_format_topic(self, gpt_response):
        """
        Busca una línea que comience con 'Topic:' en la respuesta de GPT,
        limpia caracteres no deseados, convierte a minúsculas y reemplaza
        espacios por guiones bajos.
        """
        # Dividir la respuesta de GPT en líneas
        lines = gpt_response.splitlines()

        # Buscar la línea que comienza con 'Topic:'
        for line in lines:
            if line.startswith("Topic:"):
                # Extraer el texto después de 'Topic:'
                topic = line[len("Topic:"):].strip()

                # Convertir a minúsculas, reemplazar espacios por _, y eliminar todo lo que no sea a-z o _
                formatted_topic = re.sub(r'[^a-z_]', '', topic.lower().replace(' ', '_'))

                return formatted_topic

        return None  # Si no se encuentra el topic, devolver None

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

