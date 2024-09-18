import os
import keyboard
import subprocess
import openai
from PIL import Image

class ScreenshotHandler:
    def __init__(self, config):
        self.api_key = config['openai_api_key']
        openai.api_key = self.api_key  # Configurar la API Key de OpenAI
        self.screenshot_path = 'screenshot.png'

    # Método para tomar captura de pantalla usando la herramienta nativa de macOS
    def take_screenshot(self):
        # Usamos screencapture para capturar la pantalla y guardar la imagen
        subprocess.run(['screencapture', self.screenshot_path])
        print(f"Captura de pantalla guardada en {self.screenshot_path}")
        return self.screenshot_path

    # Método para enviar la captura de pantalla a GPT-4
    def send_image_to_gpt(self, image_path):
        with open(image_path, 'rb') as image_file:
            # Enviar la imagen directamente a GPT-4
            response = openai.ImageCompletion.create(
                model="gpt-4",  # Usar GPT-4 que soporta imágenes
                file=image_file,
                prompt="Resuelve el desafío que aparece en esta captura de pantalla de manera concisa y clara."
            )
        # Obtener y retornar la respuesta de GPT
        return response['choices'][0]['message']['content']


class HotkeyManager:
    def __init__(self, screenshot_handler):
        self.screenshot_handler = screenshot_handler

    # Método para manejar la combinación de teclas y tomar la captura de pantalla
    def on_hotkey(self):
        screenshot_path = self.screenshot_handler.take_screenshot()  # Tomar captura de pantalla
        gpt_response = self.screenshot_handler.send_image_to_gpt(screenshot_path)  # Enviar captura a GPT
        print(f"Respuesta de GPT:\n{gpt_response}")

    # Método para asignar la hotkey
    def assign_hotkey(self, combination='command+shift+5'):
        keyboard.add_hotkey(combination, self.on_hotkey)
        print(f"Presiona {combination} para tomar una captura de pantalla y obtener la solución de GPT-4.")
