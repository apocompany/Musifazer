import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import cv2
import math

@dataclass
class Particle:
    x: float
    y: float
    size: float
    color: Tuple[int, int, int]
    velocity: Tuple[float, float]
    life: float
    max_life: float
    acceleration: float
    rotation: float
    shape_type: str
    wave_amplitude: float
    wave_frequency: float
    phase: float
    trail_length: float  # Para estelas
    importance: float    # Qué tan importante es el sonido
    sustain: float      # Duración del sonido
    pitch: float        # Tono del sonido
    intensity: float    # Intensidad del sonido
    has_trail: bool     # Si debe dejar estela
    trail_color: Tuple[int, int, int]  # Color de la estela

class ParticleSystem:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.particles: List[Particle] = []
        self.max_height = height * 0.95  # Usar 95% de la altura
        self.trail_history = []  # Almacenar posiciones anteriores para estelas
    
    def create_particle(self, intensity: float, frequency: float, energy: float, note_duration: float = 1.0):
        x = np.random.randint(0, self.width)
        y = self.height - np.random.randint(0, 50)
        
        # Análisis de importancia del sonido
        importance = (intensity * 0.4 + energy * 0.4 + frequency * 0.2)
        
        # Determinar si es un sonido sostenido
        is_sustained = note_duration > 0.5
        
        # Color principal basado en frecuencia y energía
        hue = int((frequency * 360) % 360)
        saturation = int(min(255, (energy * 0.7 + 0.3) * 255))
        value = int(min(255, (intensity * 0.7 + 0.3) * 255))
        color = cv2.cvtColor(np.uint8([[[hue, saturation, value]]]), cv2.COLOR_HSV2BGR)[0][0]
        
        # Color de estela (más suave y transparente)
        trail_color = tuple(int(c * 0.7) for c in color)
        
        # Velocidad base aumentada significativamente
        base_speed = 200 + intensity * 300  # Velocidad base más alta
        
        # Ajustar velocidad vertical según importancia y duración
        max_height_factor = 1.5 + importance * 2  # Permite llegar más alto
        vy_base = -base_speed * max_height_factor
        
        # Movimiento horizontal más pronunciado para sonidos sostenidos
        angle = np.random.uniform(-45, 45) if is_sustained else np.random.uniform(-30, 30)
        vx_base = base_speed * np.sin(np.radians(angle)) * (1 + note_duration * 0.5)
        
        # Ajustar velocidades con variaciones
        vx = vx_base * (1 + energy * 0.8)
        vy = vy_base * (1 + importance * 1.2)
        
        # Parámetros de movimiento ondulatorio mejorados
        wave_amplitude = 8 + energy * 20  # Mayor amplitud
        wave_frequency = 2 + frequency * 8  # Más variación en frecuencia
        
        # Vida de la partícula basada en duración e importancia
        max_life = max(2.0, note_duration * 3 * (1 + importance))
        
        # Determinar si debe dejar estela
        has_trail = is_sustained or importance > 0.7
        trail_length = note_duration * 2 if has_trail else 0
        
        particle = Particle(
            x=x,
            y=y,
            size=max(4, (intensity * energy) * 25),  # Partículas más grandes
            color=color,
            velocity=(vx, vy),
            life=1.0,
            max_life=max_life,
            acceleration=0.03 + energy * 0.08,
            rotation=np.random.rand() * 360,
            shape_type=self._get_shape_type(frequency, importance),
            wave_amplitude=wave_amplitude,
            wave_frequency=wave_frequency,
            phase=np.random.uniform(0, 2 * np.pi),
            trail_length=trail_length,
            importance=importance,
            sustain=note_duration,
            pitch=frequency,
            intensity=intensity,
            has_trail=has_trail,
            trail_color=trail_color
        )
        self.particles.append(particle)
    
    def _get_shape_type(self, frequency, importance):
        # Más variedad de formas basadas en características
        if importance > 0.8:
            return 'star'  # Sonidos más importantes son estrellas
        elif frequency > 0.7:
            return 'triangle'  # Frecuencias altas son triángulos
        elif frequency < 0.3:
            return 'square'  # Frecuencias bajas son cuadrados
        else:
            return 'circle'  # El resto son círculos
    
    def update(self, dt: float):
        new_particles = []
        for particle in self.particles:
            # Factor de tiempo para movimientos
            time_factor = (1 - particle.life) * 10
            
            # Movimiento ondulatorio mejorado para sonidos sostenidos
            wave_offset = particle.wave_amplitude * np.sin(
                particle.wave_frequency * time_factor + particle.phase
            )
            
            # Movimiento más complejo para partículas importantes
            if particle.importance > 0.7:
                wave_offset *= (1 + np.cos(time_factor * 0.5) * 0.5)
            
            # Calcular nueva posición
            new_x = particle.x + (particle.velocity[0] * dt) + (wave_offset * dt)
            new_y = particle.y + particle.velocity[1] * dt
            
            # Actualizar velocidades con resistencia variable
            resistance_x = 0.995 if particle.has_trail else 0.99
            resistance_y = 0.998 if particle.has_trail else 0.995
            
            vx = particle.velocity[0] * resistance_x
            vy = particle.velocity[1] * resistance_y
            
            # Efecto de "baile" mejorado
            dance_factor = np.sin(time_factor * 2) * particle.wave_amplitude * 0.4
            if particle.importance > 0.6:
                dance_factor *= (1 + np.sin(time_factor * 0.7) * 0.3)
            
            # Actualizar posición y velocidad
            particle.x = new_x + dance_factor * dt
            particle.y = new_y
            particle.velocity = (vx, vy)
            
            # Rotación dinámica basada en importancia
            rot_speed = 45 + abs(dance_factor)
            if particle.importance > 0.7:
                rot_speed *= 1.5
            particle.rotation += dt * rot_speed
            
            # Desvanecer gradualmente
            fade_factor = 1.0
            if particle.y < self.height * 0.05:  # Desvanecer en el 5% superior
                fade_factor = particle.y / (self.height * 0.05)
            
            # Reducción de vida más lenta para partículas importantes
            life_reduction = dt / particle.max_life
            if particle.importance > 0.7:
                life_reduction *= 0.7
            
            particle.life -= life_reduction * fade_factor
            
            # Mantener partículas dentro de los límites horizontales
            particle.x = max(0, min(self.width, particle.x))
            
            # Guardar historial para estelas si es necesario
            if particle.has_trail:
                self.trail_history.append({
                    'x': particle.x,
                    'y': particle.y,
                    'color': particle.trail_color,
                    'size': particle.size * 0.7,
                    'life': particle.life,
                    'alpha': 0.5
                })
            
            # Mantener partículas con vida
            if particle.life > 0 and particle.y >= 0:
                new_particles.append(particle)
        
        self.particles = new_particles
        
        # Actualizar y limpiar historial de estelas
        self.trail_history = [trail for trail in self.trail_history if trail['life'] > 0.1]
        for trail in self.trail_history:
            trail['life'] -= dt * 0.5
    
    def draw(self, frame: np.ndarray):
        # Dibujar primero las estelas
        for trail in self.trail_history:
            alpha = trail['alpha'] * trail['life']
            color = tuple(int(c * alpha) for c in trail['color'])
            size = int(trail['size'] * trail['life'])
            cv2.circle(frame, (int(trail['x']), int(trail['y'])), size, color, -1)
        
        # Ordenar partículas por tamaño e importancia
        sorted_particles = sorted(
            self.particles,
            key=lambda p: (p.importance, p.size),
            reverse=True
        )
        
        for particle in sorted_particles:
            alpha = particle.life
            size = int(particle.size * alpha)
            color = tuple(int(c * alpha) for c in particle.color)
            
            # Aplicar efecto de brillo para partículas importantes
            if particle.importance > 0.6 or size > 10:
                self._apply_glow(frame, particle, color, size)
            
            # Dibujar la partícula según su forma
            if particle.shape_type == 'circle':
                cv2.circle(frame, (int(particle.x), int(particle.y)), size, color, -1)
            elif particle.shape_type == 'square':
                self._draw_rotated_rect(frame, particle, size, color)
            elif particle.shape_type == 'star':
                self._draw_star(frame, (int(particle.x), int(particle.y)), 
                              size, color, particle.rotation)
            elif particle.shape_type == 'triangle':
                self._draw_triangle(frame, particle, size, color)
    
    def _draw_rotated_rect(self, frame, particle, size, color):
        center = (int(particle.x), int(particle.y))
        rect = ((particle.x, particle.y), (size*2, size*2), particle.rotation)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        cv2.drawContours(frame, [box], 0, color, -1)
    
    def _draw_triangle(self, frame, particle, size, color):
        center = np.array([particle.x, particle.y])
        angle = np.radians(particle.rotation)
        points = []
        for i in range(3):
            point_angle = angle + i * (2*np.pi/3)
            point = center + size * np.array([np.cos(point_angle), np.sin(point_angle)])
            points.append(point)
        points = np.array(points, dtype=np.int32)
        cv2.fillPoly(frame, [points], color)
    
    def _draw_star(self, frame, center, size, color, rotation):
        """Dibuja una estrella con el tamaño y rotación especificados"""
        num_points = 5  # Estrella de 5 puntas
        outer_radius = size
        inner_radius = size * 0.4  # Radio interno más pequeño para forma de estrella
        points = []
        
        # Calcular puntos de la estrella
        for i in range(num_points * 2):
            # Alternar entre radio externo e interno
            current_radius = outer_radius if i % 2 == 0 else inner_radius
            # Calcular ángulo con rotación
            angle = (i * 2 * np.pi / (2 * num_points)) + np.radians(rotation)
            
            x = center[0] + current_radius * np.cos(angle)
            y = center[1] + current_radius * np.sin(angle)
            points.append([x, y])
        
        # Convertir puntos a formato numpy y dibujar
        points = np.array(points, dtype=np.int32)
        cv2.fillPoly(frame, [points], color)
    
    def _apply_glow(self, frame, particle, color, size):
        """Aplica un efecto de brillo alrededor de la partícula"""
        glow_size = size * 2
        glow_color = tuple(int(c * 0.5) for c in color)  # Color más tenue para el brillo
        
        # Crear máscara de brillo con desenfoque gaussiano
        glow_mask = np.zeros((self.height, self.width), dtype=np.uint8)
        cv2.circle(glow_mask, (int(particle.x), int(particle.y)), glow_size, 255, -1)
        glow_mask = cv2.GaussianBlur(glow_mask, (21, 21), 0)
        
        # Aplicar brillo al frame
        for c in range(3):
            frame[:, :, c] = cv2.addWeighted(
                frame[:, :, c],
                1.0,
                glow_mask,
                glow_color[c] / 255.0 * particle.life,
                0
            )