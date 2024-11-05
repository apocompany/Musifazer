from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLabel, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ..audio.processor import AudioProcessor
from ..video.generator import VideoGenerator
from ..utils.file_handler import FileHandler
from .progress_bar import ProgressBar
import os

class VideoGeneratorThread(QThread):
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, audio_path: str, output_path: str):
        super().__init__()
        self.audio_path = audio_path
        self.output_path = output_path
        
    def run(self):
        try:
            # Procesar audio
            self.progress_updated.emit(0, "Procesando audio...")
            processor = AudioProcessor(self.audio_path)
            audio_features = processor.process_audio()
            
            # Generar video
            self.progress_updated.emit(20, "Iniciando generación de video...")
            generator = VideoGenerator()
            generator.generate_video(
                audio_features,
                self.output_path,
                lambda progress, status: self.progress_updated.emit(20 + int(progress * 0.8), status)
            )
            
            self.finished.emit(self.output_path)
            
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizador Musical")
        self.setMinimumSize(800, 600)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Componentes de la UI
        self.upload_button = QPushButton("Subir Audio")
        self.upload_button.clicked.connect(self.upload_audio)
        
        # Añadir label para mostrar el archivo seleccionado
        self.file_label = QLabel("Ningún archivo seleccionado")
        self.file_label.setAlignment(Qt.AlignCenter)
        
        # Añadir botón para limpiar selección
        self.clear_button = QPushButton("Limpiar selección")
        self.clear_button.clicked.connect(self.clear_selection)
        self.clear_button.setEnabled(False)
        
        self.create_video_button = QPushButton("Crear Video Musical")
        self.create_video_button.clicked.connect(self.create_video)
        self.create_video_button.setEnabled(False)
        
        self.progress_bar = ProgressBar()
        self.progress_bar.hide()
        
        # Agregar componentes al layout
        layout.addWidget(self.upload_button)
        layout.addWidget(self.file_label)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.create_video_button)
        layout.addWidget(self.progress_bar)
        
        self.audio_path = None
        self.generator_thread = None
    
    def clear_selection(self):
        self.audio_path = None
        self.file_label.setText("Ningún archivo seleccionado")
        self.create_video_button.setEnabled(False)
        self.clear_button.setEnabled(False)
    
    def upload_audio(self):
        if self.audio_path:  # Si ya hay un archivo seleccionado
            reply = QMessageBox.question(
                self,
                "Archivo existente",
                "Ya hay un archivo seleccionado. ¿Desea reemplazarlo?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo de audio",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.m4a)"
        )
        
        if file_path:
            self.audio_path = file_path
            self.file_label.setText(f"Archivo seleccionado: {os.path.basename(file_path)}")
            self.create_video_button.setEnabled(True)
            self.clear_button.setEnabled(True)
    
    def create_video(self):
        if not self.audio_path:
            return
            
        # Deshabilitar botones durante el procesamiento
        self.upload_button.setEnabled(False)
        self.create_video_button.setEnabled(False)
        self.progress_bar.show()
        
        # Preparar ruta de salida
        output_path = FileHandler.get_output_path(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            os.path.basename(self.audio_path)
        )
        
        # Iniciar procesamiento en thread separado
        self.generator_thread = VideoGeneratorThread(self.audio_path, output_path)
        self.generator_thread.progress_updated.connect(self.update_progress)
        self.generator_thread.finished.connect(self.process_completed)
        self.generator_thread.error.connect(self.process_error)
        self.generator_thread.start()
    
    def update_progress(self, value: int, status: str):
        self.progress_bar.update_progress(value, status)
    
    def process_completed(self, output_path: str):
        self.upload_button.setEnabled(True)
        self.create_video_button.setEnabled(True)
        self.progress_bar.hide()
        
        QMessageBox.information(
            self,
            "Proceso Completado",
            f"Video generado exitosamente en:\n{output_path}"
        )
    
    def process_error(self, error_message: str):
        self.upload_button.setEnabled(True)
        self.create_video_button.setEnabled(True)
        self.progress_bar.hide()
        
        QMessageBox.critical(
            self,
            "Error",
            f"Error durante el procesamiento:\n{error_message}"
        )