import configparser
import os

project_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(project_dir, 'config.ini')
config = configparser.ConfigParser()
config.read(config_path)
