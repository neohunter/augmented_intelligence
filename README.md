# Real-time Conversation Assistant Aka. Augmented Interaction

This project provides contextual assistance during real-time conversations. The AI-powered assistant listens to the conversation and offers valuable insights, including:

- Suggesting follow-up questions.
- Providing additional information related to the conversation topics.
- Identifying and answering questions that arise during the discussion.
- Records a cloud of tags for futher discussion..

The application enhances the quality and depth of conversations by offering real-time, contextual support to the user. It leverages advanced AI technologies for speech recognition, natural language processing, and contextual understanding to deliver timely and relevant assistance.

This tool is ideal for professionals, researchers, or anyone looking to augment their conversational capabilities with AI-powered insights and information retrieval.

## Requirements

- Python 3.x
- pip

## Installation

1. Clone this repository:
```bash
git clone https://github.com/neohunter/transcription_project.git
cd transcription_project
```

Install the dependencies:

For macOS:
```bash
brew install portaudio
```

For Ubuntu:
```bash
sudo apt install libasound2-dev portaudio19-dev python3-pyaudio
```

```bash
pip install -r requirements.txt
Set your API keys in `config.yml`.
```

Run the application:
```bash
python src/main.py
```

## Testing

To run the tests, use the following command:

```bash
python -m unittest discover -s tests
```

### Create and activate a virtual environment

You can create a virtual environment to install the dependencies and keep your environment clean.

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

## Running the project:

If you are using conda:

```bash
conda env create -f environment.yml
conda activate augmented_intelligence
python src/main.py
```

If you are using pip:

```bash
pip install -r requirements.txt
python src/main.py
```

# Other Tools and Libraries

* https://github.com/juanmc2005/diart
