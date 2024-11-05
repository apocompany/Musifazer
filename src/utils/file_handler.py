import os
from typing import List
import shutil

class FileHandler:
    @staticmethod
    def create_temp_directory(base_path: str) -> str:
        temp_dir = os.path.join(base_path, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    @staticmethod
    def clean_temp_directory(temp_dir: str):
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
    
    @staticmethod
    def get_output_path(base_path: str, filename: str) -> str:
        output_dir = os.path.join(base_path, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generar nombre único
        base_name = os.path.splitext(filename)[0]
        counter = 1
        output_path = os.path.join(output_dir, f"{base_name}_visual.mp4")
        
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{base_name}_visual_{counter}.mp4")
            counter += 1
            
        return output_path 