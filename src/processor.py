# from openai import OpenAI

from openai import OpenAI
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
import json

# ToDo: Ask GPT to identify new topic and notify transcriber about that.

# gpt-4o-mini lower cost

class Processor:
    def __init__(self, config):
        self.config = config
        self.api_key = config['openai']['api_key']
        self.prompt_template = config[config['general_settings']['prompt_to_use']]
        # self.client = OpenAI(api_key=config['openai']['api_key'])
        self.client = OpenAI(
            api_key=self.api_key,
        )

    def process_transcription(self, transcription):
        print(":::::::::::::::::")
        response = self.client.chat.completions.create(
            model=self.config['general_settings']['gpt_model'],
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides context and answers questions. Be as concise as possible, do not greet or explain your process. Do not rephrase the transcript or the input receive. Provide straight to the point information."
                },
                {
                    "role": "user",
                    # "content": self.prompt_template.format(transcription=transcription)
                    "content": self.prompt_template + "\nTranscription: " + transcription
                }
            ],
            max_tokens=self.config['general_settings']['max_tokens'],
            temperature=self.config['general_settings']['temperature']
        )

        # print("----------------GPT REQUEST------------------")
        # print(self.prompt_template + "\nTranscription: " + transcription)
        # print("----------------END GPT REQUEST------------------")

        # print("----------------GPT RESPONSE----------------")
        # print(response)
        # print("----------------END GPT RESPONSE----------------")

        response = response.choices[0].message.content.strip()

        return response



    def process(self, text):
        print("-------------------------------- EXECUTING USING DAVINCI --------------------------------")
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

    def parse_gpt_response(self, gpt_response):
        """
        Parses the GPT response to extract the topic, key concepts, questions,
        follow-up questions, and keywords for the current section of the conversation.

        Args:
            gpt_response (str): The raw GPT response in JSON-like string format.

        Returns:
            dict: A dictionary containing the extracted 'topic', 'key_concepts',
                'questions', 'follow_up_questions', and 'keywords'.
        """
        try:
            # Convert the GPT response string to a JSON object
            response_data = json.loads(gpt_response)

            # Initialize default values for each section
            topic = ""
            key_concepts = []
            questions = []
            follow_up_questions = []
            keywords = []

            # Extract the current section's information
            conversation = response_data.get("conversation", {})
            current_section = conversation.get("current_section", {})

            # Extract topic
            topic = current_section.get("topic", "")

            # Extract key concepts
            for concept_data in current_section.get("key_concepts", []):
                key_concepts.append({
                    "concept": concept_data.get("concept", ""),
                    "description": concept_data.get("description", ""),
                    "emoji": concept_data.get("emoji", "")
                })

            # Extract questions and answers
            for question_data in current_section.get("questions", []):
                questions.append({
                    "question": question_data.get("question", ""),
                    "answer": question_data.get("answer", "")
                })

            # Extract follow-up questions and answers
            for follow_up_data in current_section.get("follow_up_questions", []):
                follow_up_questions.append({
                    "question": follow_up_data.get("question", ""),
                    "answer": follow_up_data.get("answer", "")
                })

            # Extract keywords (word cloud)
            keywords = current_section.get("keywords", [])

            # Return all extracted data in a dictionary
            return {
                "topic": topic,
                "key_concepts": key_concepts,
                "questions": questions,
                "follow_up_questions": follow_up_questions,
                "keywords": keywords
            }

        except json.JSONDecodeError as e:
            print(f"🛑 Error parsing GPT response: {e}")
            return {
                "topic": "",
                "key_concepts": [],
                "questions": [],
                "follow_up_questions": [],
                "keywords": []
            }
