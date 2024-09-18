# from openai import OpenAI

from openai import OpenAI
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

# ToDo: Ask GPT to identify new topic and notify transcriber about that.

# gpt-4o-mini lower cost

class Processor:
    def __init__(self, config):
        self.api_key = config['openai']['api_key']
        self.prompt_template = config['gpt_prompt_b']
        # self.client = OpenAI(api_key=config['openai']['api_key'])
        self.client = OpenAI(
            api_key=self.api_key,
        )

    def process_transcription(self, transcription):
        print(":::::::::::::::::")
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides context and answers questions. Be as concise as possible, do not greet or explain your process. Do not rephrase the transcript or the input receive. Provide straight to the point information."
                },
                {
                    "role": "user",
                    "content": self.prompt_template.format(transcription=transcription)
                }
            ],
            max_tokens=150,
            temperature=0.7
        )
        response = response.choices[0].message.content.strip()
        print("--------------------------------")
        return response



    def process(self, text):
        response = self.client.completions.create(
            engine="davinci",
            prompt=f"Contextualize this conversation and provide a word cloud and answer any questions:\n\n{text}",
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7
        )
        gpt_response = response.choices[0].text.strip()

        wordcloud = WordCloud(width=800, height=400).generate(text)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()

        return gpt_response
