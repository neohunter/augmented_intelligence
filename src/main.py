from transcriber import Transcriber
from processor import Processor
from utils import load_config

# TODO: Give context to the conversation that will take place and explain the kind
#   of support that you are looking for by the AI.
# TODO: Record audio
# TODO: save transcript to file

def main():
    config = load_config()
    print("Starting real-time transcription...\r\n")

    transcriber = Transcriber(config)
    processor = Processor(config)

    transcriber.processor = processor  # Pasar el processor al transcriber para consultas GPT
    transcriber.start()  # Comenzar la transcripción

    # async for text in transcriber.transcribe():
    #     response = processor.process(text)
    #     print(response)

    # use_microphone = True

    # if use_microphone:
    #     transcription = transcriber.transcribe(use_microphone=True)
    # else:
    #     audio_stream_url = "ruta_a_tu_audio_en_vivo"
    #     transcription = transcriber.transcribe(audio_stream=audio_stream_url, use_microphone=False)

    # print(f"Transcripción: {transcription}")

    # result = processor.process_transcription(transcription)
    # print(f"Resultado de GPT: {result}")


if __name__ == "__main__":
    main()
