import cv2
import numpy as np
from ..audio.processor import AudioProcessor
from .particles import ParticleSystem
from typing import Callable
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
import os

class VideoGenerator:
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.particle_system = ParticleSystem(width, height)
    
    def _estimate_note_duration(self, frame_num: int, rms: np.ndarray, window_size: int = 10) -> float:
        """Estima la duración de la nota actual basada en la energía del audio"""
        start_idx = max(0, frame_num - window_size)
        end_idx = min(len(rms), frame_num + window_size)
        
        # Buscar hacia adelante para encontrar la duración de la nota
        current_rms = rms[frame_num]
        threshold = current_rms * 0.7  # 70% del valor actual
        
        duration = 0
        for i in range(frame_num, end_idx):
            if rms[i] >= threshold:
                duration += 1
            else:
                break
        
        return duration / self.fps  # Convertir frames a segundos
    
    def generate_video(self, audio_features: dict, output_path: str, 
                      progress_callback: Callable[[int, str], None]):
        # Crear video temporal sin audio
        temp_video_path = output_path + "_temp.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video_path, fourcc, self.fps, (self.width, self.height))
        
        duration = audio_features['duration']
        total_frames = int(duration * self.fps)
        
        # Interpolar características
        frames_times = np.linspace(0, duration, total_frames)
        audio_times = np.linspace(0, duration, len(audio_features['rms']))
        
        rms = np.interp(frames_times, audio_times, audio_features['rms'])
        spec_centroids = np.interp(frames_times, audio_times, audio_features['spectral_centroids'])
        spec_rolloff = np.interp(frames_times, audio_times, audio_features['spectral_rolloff'])
        
        # Normalizar características
        rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-6)
        spec_norm = (spec_centroids - spec_centroids.min()) / (spec_centroids.max() - spec_centroids.min() + 1e-6)
        energy_norm = (spec_rolloff - spec_rolloff.min()) / (spec_rolloff.max() - spec_rolloff.min() + 1e-6)
        
        prev_frame = None
        
        # Añadir un fondo gradual
        background = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        for frame_num in range(total_frames):
            # Crear frame con fondo gradual
            frame = background.copy()
            
            # Obtener características normalizadas
            intensity = rms_norm[frame_num]
            frequency = spec_norm[frame_num]
            energy = energy_norm[frame_num]
            
            # Estimar duración de la nota actual
            note_duration = self._estimate_note_duration(frame_num, rms_norm)
            
            # Crear partículas
            base_particles = 10
            energy_boost = energy * 30
            intensity_boost = intensity * 20
            num_particles = int(base_particles + energy_boost + intensity_boost)
            
            for _ in range(num_particles):
                self.particle_system.create_particle(
                    intensity=intensity,
                    frequency=frequency,
                    energy=energy,
                    note_duration=note_duration
                )
            
            # Actualizar y dibujar partículas
            self.particle_system.update(1.0 / self.fps)
            self.particle_system.draw(frame)
            
            # Mejorar el efecto de desvanecimiento
            if prev_frame is not None:
                # Ajustar la mezcla basada en la energía
                blend_factor = 0.85 - (energy * 0.3)  # Más energía = menos rastro
                frame = cv2.addWeighted(frame, blend_factor, prev_frame, 1 - blend_factor, 0)
            
            prev_frame = frame.copy()
            
            # Aplicar un poco de desenfoque para suavizar
            frame = cv2.GaussianBlur(frame, (3, 3), 0)
            
            out.write(frame)
            
            progress = int((frame_num + 1) / total_frames * 80)
            progress_callback(progress, f"Generando video: {progress}%")
        
        out.release()
        
        # Combinar video con audio usando moviepy
        progress_callback(90, "Combinando video con audio...")
        try:
            video = VideoFileClip(temp_video_path)
            audio = AudioFileClip(audio_features['audio_path'])
            
            final_video = video.set_audio(audio)
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=output_path + "_temp_audio.m4a",
                remove_temp=True
            )
            
            # Limpiar
            video.close()
            audio.close()
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
                
            progress_callback(100, "¡Video completado!")
            
        except Exception as e:
            raise Exception(f"Error al combinar audio y video: {str(e)}")