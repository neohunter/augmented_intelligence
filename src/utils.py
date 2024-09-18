import yaml
import os

def load_config():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config.yml')

    with open(config_path, 'r') as stream:
        config = yaml.safe_load(stream)
    return config
