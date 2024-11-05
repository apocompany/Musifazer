from PyQt5.QtWidgets import QProgressBar, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class ProgressBar(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Preparando...")
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
    
    def update_progress(self, value, status):
        self.progress.setValue(value)
        self.status_label.setText(status) 