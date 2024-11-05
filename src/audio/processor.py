import librosa
import numpy as np
from typing import Tuple, Dict

class AudioProcessor:
    def __init__(self, audio_path: str):
        self.audio_path = audio_path
        self.y = None
        self.sr = None
        self.tempo = None
        self.beat_frames = None
        self.spectral_centroids = None
        self.spectral_rolloff = None
        
    def process_audio(self) -> Dict:
        """Procesa el archivo de audio y extrae características"""
        # Cargar archivo de audio
        self.y, self.sr = librosa.load(self.audio_path)
        
        # Obtener tempo y beats
        self.tempo, self.beat_frames = librosa.beat.beat_track(y=self.y, sr=self.sr)
        
        # Obtener características espectrales
        self.spectral_centroids = librosa.feature.spectral_centroid(y=self.y, sr=self.sr)[0]
        self.spectral_rolloff = librosa.feature.spectral_rolloff(y=self.y, sr=self.sr)[0]
        
        # Obtener cromagrama
        chromagram = librosa.feature.chroma_stft(y=self.y, sr=self.sr)
        
        # Obtener energía por frame
        rms = librosa.feature.rms(y=self.y)[0]
        
        return {
            'tempo': self.tempo,
            'beat_frames': self.beat_frames,
            'spectral_centroids': self.spectral_centroids,
            'spectral_rolloff': self.spectral_rolloff,
            'chromagram': chromagram,
            'rms': rms,
            'duration': len(self.y) / self.sr,
            'sample_rate': self.sr,
            'audio_path': self.audio_path
        } 