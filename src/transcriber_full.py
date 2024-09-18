import asyncio
import websockets
import requests
from openai import OpenAI

client = OpenAI(api_key=openai_api_key)
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

# Configuración de API keys
assemblyai_api_key = 'YOUR_ASSEMBLYAI_API_KEY'
openai_api_key = 'YOUR_OPENAI_API_KEY'


async def transcribe_and_process():
    async with websockets.connect('wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000',
                                  extra_headers={'Authorization': assemblyai_api_key}) as websocket:

        # Mantenemos la conexión abierta y procesamos el audio en tiempo real
        while True:
            try:
                result = await websocket.recv()
                data = result.get('text', '')

                if data:
                    print(f"Transcribed: {data}")

                    # Enviar a GPT-3 para procesar y generar contexto y respuestas
                    response = client.completions.create(engine="davinci",
                    prompt=f"Contextualize this conversation and provide a word cloud and answer any questions:\n\n{data}",
                    max_tokens=150,
                    n=1,
                    stop=None,
                    temperature=0.7)
                    gpt_response = response.choices[0].text.strip()

                    print(f"GPT-3 Response: {gpt_response}")

                    # Generar nube de palabras
                    wordcloud = WordCloud(width=800, height=400).generate(data)
                    plt.figure(figsize=(10, 5))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis("off")

                    # Guardar la imagen en memoria y mostrarla
                    buf = BytesIO()
                    plt.savefig(buf, format='PNG')
                    buf.seek(0)
                    img = Image.open(buf)
                    img.show()

            except websockets.ConnectionClosedError:
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(transcribe_and_process())
