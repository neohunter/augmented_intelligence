# Real-time Conversation Assistant Aka. Augmented Interaction

This project provides contextual assistance during real-time conversations. The AI-powered assistant listens to the conversation and offers valuable insights, including:

- Suggesting follow-up questions
- Providing additional information related to the conversation topics
- Identifying and answering questions that arise during the discussion
- Records a cloud of tags for futher discussion.

The application enhances the quality and depth of conversations by offering real-time, contextual support to the user. It leverages advanced AI technologies for speech recognition, natural language processing, and contextual understanding to deliver timely and relevant assistance.

This tool is ideal for professionals, researchers, or anyone looking to augment their conversational capabilities with AI-powered insights and information retrieval.

## Requisitos

- Python 3.x
- pip

## Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/neohunter/transcription_project.git
   cd transcription_project

Instala las dependencias:

bash
(brew apt etc) install portaudio
pip install -r requirements.txt
Configura tus API keys en src/transcriber.py.

Ejecuta la aplicación:

bash
python src/transcriber.py

Pruebas
Para ejecutar las pruebas, usa el siguiente comando:

bash
python -m unittest discover -s tests
bash

### 7. Crear un entorno virtual y activar

Puedes crear un entorno virtual para instalar las dependencias y mantener el entorno limpio.

```bash
python -m venv venv
source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
pip install -r requirements.txt

3. Ejecución del proyecto:
Si usas conda:

```bash
conda env create -f environment.yml
conda activate augmented_intelligence
python src/main.py
```


Si usas pip:

```bash
pip install -r requirements.txt
python src/main.py
```
