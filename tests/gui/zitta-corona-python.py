import sys
import math
import random
from dataclasses import dataclass
from typing import List, Tuple
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath

# 색상 설정
BACKGROUND = QColor(8, 8, 12)
MAIN_PINK = QColor(255, 106, 138)
SUB_RED = QColor(255, 46, 46)
HIGHLIGHT = QColor(243, 244, 246)

# 설정
CENTER_X, CENTER_Y = 400, 400
BASE_RADIUS = 150
RIBBON_STRAND_COUNT = 12
RIBBON_OPACITY = 20

# 상태별 파티클 설정
PARTICLE_CONFIG = {
    'idle': {'count': 150, 'speed': 0.3, 'spread': 0.4},
    'wake': {'count': 250, 'speed': 0.5, 'spread': 0.6},
    'thinking': {'count': 400, 'speed': 0.7, 'spread': 1.0},
    'resolve': {'count': 100, 'speed': 0.2, 'spread': 0.3}
}


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color_mix: float
    return_to_center: bool


@dataclass
class RibbonPoint:
    angle: float
    phase: float


@dataclass
class RibbonStrand:
    points: List[RibbonPoint]
    opacity: float
    color_mix: float


@dataclass
class Spark:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    length: float


def lerp_color(color1: QColor, color2: QColor, t: float) -> QColor:
    """두 색상 사이를 보간"""
    return QColor(
        int(color1.red() + (color2.red() - color1.red()) * t),
        int(color1.green() + (color2.green() - color1.green()) * t),
        int(color1.blue() + (color2.blue() - color1.blue()) * t)
    )


def create_particle(angle: float, radius: float, state: str) -> Particle:
    """새로운 파티클 생성"""
    config = PARTICLE_CONFIG[state]
    
    x = CENTER_X + math.cos(angle) * radius
    y = CENTER_Y + math.sin(angle) * radius
    
    tangent_angle = angle + math.pi / 2
    outward_angle = angle
    
    tangent_speed = config['speed'] * (0.3 + random.random() * 0.4)
    outward_speed = config['speed'] * config['spread'] * (0.2 + random.random() * 0.3)
    
    brownian_x = (random.random() - 0.5) * 0.1
    brownian_y = (random.random() - 0.5) * 0.1
    
    vx = math.cos(tangent_angle) * tangent_speed + math.cos(outward_angle) * outward_speed + brownian_x
    vy = math.sin(tangent_angle) * tangent_speed + math.sin(outward_angle) * outward_speed + brownian_y
    
    return Particle(
        x=x,
        y=y,
        vx=vx,
        vy=vy,
        life=1.0,
        max_life=180 + random.random() * 120,
        size=1.0 + random.random() * 2.0,
        color_mix=0 if random.random() < 0.8 else random.random() * 0.3,
        return_to_center=state == 'thinking' and random.random() < 0.15
    )


def create_ribbon_strand(index: int, total: int) -> RibbonStrand:
    """리본 스트랜드 생성"""
    points = []
    segments = 120
    phase_offset = (index / total) * math.pi * 2
    
    for i in range(segments + 1):
        angle = (i / segments) * math.pi * 2
        points.append(RibbonPoint(angle=angle, phase=phase_offset))
    
    return RibbonStrand(
        points=points,
        opacity=RIBBON_OPACITY * (0.7 + random.random() * 0.3),
        color_mix=index / total * 0.2
    )


def create_spark() -> Spark:
    """스파크 생성"""
    angle = random.random() * math.pi * 2
    radius = BASE_RADIUS + (random.random() - 0.5) * 20
    
    return Spark(
        x=CENTER_X + math.cos(angle) * radius,
        y=CENTER_Y + math.sin(angle) * radius,
        vx=math.cos(angle) * (1 + random.random()),
        vy=math.sin(angle) * (1 + random.random()),
        life=1.0,
        max_life=20 + random.random() * 15,
        length=3 + random.random() * 5
    )


class ZittaCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(800, 800)
        self.state = 'idle'
        self.time = 0
        self.particles: List[Particle] = []
        self.ribbon_strands: List[RibbonStrand] = []
        self.sparks: List[Spark] = []
        
        # 리본 스트랜드 초기화
        for i in range(RIBBON_STRAND_COUNT):
            self.ribbon_strands.append(create_ribbon_strand(i, RIBBON_STRAND_COUNT))
        
        # 초기 파티클 생성
        for _ in range(PARTICLE_CONFIG['idle']['count']):
            angle = random.random() * math.pi * 2
            radius = BASE_RADIUS + (random.random() - 0.5) * 10
            self.particles.append(create_particle(angle, radius, 'idle'))
        
        # 타이머 설정
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS
    
    def update_animation(self):
        """애니메이션 업데이트"""
        self.time += 1
        config = PARTICLE_CONFIG[self.state]
        
        # 파티클 추가
        while len(self.particles) < config['count']:
            angle = random.random() * math.pi * 2
            radius = BASE_RADIUS + (random.random() - 0.5) * 10
            self.particles.append(create_particle(angle, radius, self.state))
        
        # 파티클 업데이트
        active_particles = []
        for p in self.particles:
            # 브라운 운동
            p.vx += (random.random() - 0.5) * 0.03
            p.vy += (random.random() - 0.5) * 0.03
            
            # 중심으로 회귀
            if p.return_to_center:
                dx = CENTER_X - p.x
                dy = CENTER_Y - p.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 50:
                    p.vx += dx / dist * 0.01
                    p.vy += dy / dist * 0.01
            
            # 속도 감쇠
            p.vx *= 0.99
            p.vy *= 0.99
            
            # 위치 업데이트
            p.x += p.vx
            p.y += p.vy
            p.life -= 1
            
            if p.life > 0:
                active_particles.append(p)
        
        self.particles = active_particles
        
        # 스파크 생성
        if random.random() < 0.01 and self.state != 'resolve':
            self.sparks.append(create_spark())
        
        # 스파크 업데이트
        active_sparks = []
        for s in self.sparks:
            s.x += s.vx
            s.y += s.vy
            s.life -= 1
            if s.life > 0:
                active_sparks.append(s)
        
        self.sparks = active_sparks
        
        self.update()
    
    def paintEvent(self, event):
        """그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 배경
        painter.fillRect(self.rect(), BACKGROUND)
        
        # 트레일 효과를 위한 반투명 배경
        fade_color = QColor(8, 8, 12, 38)
        painter.fillRect(self.rect(), fade_color)
        
        # 펄스 효과
        pulse_scale = 1.0
        if self.state == 'idle':
            pulse_scale = 1.0 + math.sin(self.time * 0.01) * 0.005
        elif self.state == 'wake':
            pulse_scale = 1.0 + math.sin(self.time * 0.05) * 0.015
        
        # 가산 블렌딩 모드
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        
        # 리본 스트랜드 그리기
        for strand in self.ribbon_strands:
            path = QPainterPath()
            first_point = True
            
            for point in strand.points:
                wave_offset = math.sin(self.time * 0.0003 + point.phase + point.angle * 3) * 3
                radius = (BASE_RADIUS + wave_offset) * pulse_scale
                x = CENTER_X + math.cos(point.angle) * radius
                y = CENTER_Y + math.sin(point.angle) * radius
                
                if first_point:
                    path.moveTo(x, y)
                    first_point = False
                else:
                    path.lineTo(x, y)
            
            # 리본 색상
            color = lerp_color(MAIN_PINK, SUB_RED, strand.color_mix)
            color.setAlpha(int(strand.opacity))
            
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.drawPath(path)
        
        # 파티클 그리기
        for p in self.particles:
            alpha = min(1.0, p.life / p.max_life)
            fade_alpha = alpha / 0.3 if alpha < 0.3 else 1.0
            
            color = lerp_color(MAIN_PINK, SUB_RED, p.color_mix)
            color.setAlpha(int(fade_alpha * 200))
            
            brush = QBrush(color)
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            
            # 원형 파티클
            painter.drawEllipse(
                QPointF(p.x, p.y),
                p.size,
                p.size
            )
        
        # 스파크 그리기
        for s in self.sparks:
            alpha = s.life / s.max_life
            color = QColor(HIGHLIGHT)
            color.setAlpha(int(alpha * 100))
            
            pen = QPen(color, 1)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(s.x, s.y),
                QPointF(s.x - s.vx * s.length, s.y - s.vy * s.length)
            )
        
        painter.end()
    
    def set_state(self, new_state: str):
        """상태 변경"""
        self.state = new_state


class ZittaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZiTTA 코로나 애니메이션")
        self.setStyleSheet("background-color: #08080C;")
        
        # 메인 위젯
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 레이아웃
        layout = QVBoxLayout()
        
        # 캔버스
        self.canvas = ZittaCanvas()
        layout.addWidget(self.canvas, alignment=Qt.AlignCenter)
        
        # 상태 레이블
        self.state_label = QLabel("현재 상태: IDLE")
        self.state_label.setStyleSheet("color: #FF6A8A; font-size: 18px; font-weight: bold; padding: 10px;")
        self.state_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.state_label)
        
        # 정보 레이블
        self.info_label = QLabel("💭 Idle: 미세한 호흡, 차분한 존재감")
        self.info_label.setStyleSheet("color: #FF6A8A; font-size: 14px; padding: 5px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 상태 버튼들
        self.state_buttons = {}
        states = [
            ('idle', 'Idle', '💭 Idle: 미세한 호흡, 차분한 존재감'),
            ('wake', 'Wake', '👁️ Wake: 집중하며 깨어남'),
            ('thinking', 'Thinking', '🔥 Thinking: 사고가 열로 확산되며 흐름'),
            ('resolve', 'Resolve', '✨ Resolve: 생각 정리 완료')
        ]
        
        for state, label, info in states:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1f1f23;
                    color: #999;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2a2a2f;
                }
                QPushButton:pressed {
                    background-color: #FF6A8A;
                }
            """)
            btn.clicked.connect(lambda checked, s=state, i=info: self.change_state(s, i))
            button_layout.addWidget(btn)
            self.state_buttons[state] = btn
        
        # 초기 활성 버튼 스타일
        self.state_buttons['idle'].setStyleSheet("""
            QPushButton {
                background-color: #FF6A8A;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        layout.addLayout(button_layout)
        main_widget.setLayout(layout)
        
        self.current_state = 'idle'
    
    def change_state(self, state: str, info: str):
        """상태 변경"""
        self.canvas.set_state(state)
        self.state_label.setText(f"현재 상태: {state.upper()}")
        self.info_label.setText(info)
        self.current_state = state
        
        # 버튼 스타일 업데이트
        for s, btn in self.state_buttons.items():
            if s == state:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FF6A8A;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1f1f23;
                        color: #999;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 24px;
                        font-weight: bold;
                        font-size: 14px;
                    }
                    QPushButton:hover {
                        background-color: #2a2a2f;
                    }
                """)
        
        # Resolve 상태면 3초 후 Idle로 복귀
        if state == 'resolve':
            QTimer.singleShot(3000, lambda: self.change_state('idle', '💭 Idle: 미세한 호흡, 차분한 존재감'))


def main():
    app = QApplication(sys.argv)
    window = ZittaMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
