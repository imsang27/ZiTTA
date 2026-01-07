import math
import random
import sys
from dataclasses import dataclass

from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QRadialGradient
from PyQt6.QtWidgets import QApplication, QWidget


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    age: float
    size: float          # 아주 작게(0.4~1.2)
    seed: float
    warm: float          # 0..1 (핑크->레드 비율)
    orbit: float         # 0..1 (wake에서 일부만)
    pull: float          # 중심 회귀 성향
    kind: int            # 0: dust, 1: flare spark


class ZiTTACoronaWidget(QWidget):
    # 상태
    IDLE = "idle"
    WAKE = "wake"
    THINK = "think"
    RESOLVE = "resolve"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZiTTA Corona Dust (PyQt)")
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # 타이밍
        self.fps = 60
        self.dt = 1.0 / self.fps
        self.t = 0.0          # global time
        self.state = self.IDLE
        self.state_t = 0.0

        # 파티클
        self.particles: list[Particle] = []
        self.max_particles = 1200  # 먼지 느낌은 개체수로 만든다 (하지만 과하면 CPU/렌더 부담)
        self.resolve_target = 120

        # 색 (코로나/열복사 톤)
        self.bg = QColor(11, 14, 20)
        self.ring_color = QColor(243, 244, 246)
        self.pink = QColor(255, 106, 138)
        self.red = QColor(255, 46, 46)

        # 링 파라미터
        self.ring_ratio = 0.18
        self.ring_thickness = 1.6  # 얇게
        self.idle_pulse_amp = 0.008
        self.idle_pulse_speed = 0.7
        self.wake_breath_amp = 0.040
        self.wake_breath_dur = 1.2

        # 스폰 레이트 (/sec)
        self.idle_rate = 90        # "미세먼지"는 적은 수가 아니라 '많고 희미한 수'
        self.wake_rate = 210
        self.think_rate = 280
        self.resolve_rate = 8

        self.spawn_acc = 0.0
        self.resolve_kick = 0.0

        # 플레어(가끔씩 얇은 스파크)
        self.flare_cooldown = 0.0

        # 타이머
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)
        self.timer.start(int(1000 / self.fps))

        # 초기 시드(처음부터 살아있는 느낌)
        self.seed_initial()

    # ------------------ 상태 제어 ------------------
    def set_state(self, s: str):
        if s not in (self.IDLE, self.WAKE, self.THINK, self.RESOLVE):
            return
        self.state = s
        self.state_t = 0.0

        if s == self.WAKE:
            # 내부 밀도 순간 증가
            self.burst(160, where="inside", warm=0.45, orbit_bias=0.8)
        elif s == self.RESOLVE:
            self.resolve_kick = 1.0

    # ------------------ 초기 파티클 ------------------
    def seed_initial(self):
        cx, cy, r = self.scene_params()
        for _ in range(520):
            self.spawn_particle(cx, cy, r, where="rim", warm=0.15)

    # ------------------ 씬 파라미터 ------------------
    def scene_params(self):
        w = max(1, self.width())
        h = max(1, self.height())
        cx = w * 0.5
        cy = h * 0.5
        r = min(w, h) * self.ring_ratio
        return cx, cy, r

    # ------------------ 노이즈(난류) ------------------
    # Perlin 대신 sin/cos 혼합 pseudo-flow. "코로나"는 이런 미세 난류가 핵심.
    def flow(self, t: float, seed: float):
        x = math.sin(t * 1.8 + seed * 10.7) * 0.65 + math.sin(t * 0.85 + seed * 3.1) * 0.35
        y = math.cos(t * 1.4 + seed * 7.9) * 0.65 + math.cos(t * 0.78 + seed * 5.3) * 0.35
        return x, y

    # ------------------ 스폰 ------------------
    def mix_color(self, warm: float) -> QColor:
        warm = clamp01(warm)
        r = int(lerp(self.pink.red(), self.red.red(), warm))
        g = int(lerp(self.pink.green(), self.red.green(), warm))
        b = int(lerp(self.pink.blue(), self.red.blue(), warm))
        return QColor(r, g, b)

    def spawn_particle(self, cx: float, cy: float, r: float, where: str, warm: float, orbit_bias: float = 0.0):
        ang = random.random() * math.tau

        if where == "rim":
            rr = r + random.uniform(-1.2, 1.2)
            x = cx + math.cos(ang) * rr
            y = cy + math.sin(ang) * rr
        else:
            # 내부 생성
            rr = math.sqrt(random.random()) * (r * 0.95)
            x = cx + math.cos(ang) * rr
            y = cy + math.sin(ang) * rr

        # "열복사/코로나"는 직선으로 튀면 망한다 → 기본 속도는 작고, 난류/곡선이 주인공
        out = 10 if where == "rim" else 14
        tx = -math.sin(ang)
        ty = math.cos(ang)

        vx = math.cos(ang) * out + tx * random.uniform(-8, 8) + random.uniform(-3, 3)
        vy = math.sin(ang) * out + ty * random.uniform(-8, 8) + random.uniform(-3, 3)

        # 먼지: 매우 작고 오래감
        size = random.uniform(0.35, 1.1)
        life = random.uniform(2.8, 5.8) if where == "rim" else random.uniform(2.2, 5.0)

        orbit = 0.0
        if self.state == self.WAKE:
            # 일부만 궤도
            orbit = clamp01(random.random() * orbit_bias)

        p = Particle(
            x=x, y=y, vx=vx, vy=vy,
            life=life, age=0.0,
            size=size,
            seed=random.random() * 999.0,
            warm=warm,
            orbit=orbit,
            pull=random.uniform(0.10, 0.30),
            kind=0
        )
        self.particles.append(p)
        if len(self.particles) > self.max_particles:
            # 오래된 것부터 조금씩 제거
            self.particles = self.particles[-self.max_particles :]

    def spawn_flare(self, cx: float, cy: float, r: float):
        # 얇은 스파크/플레어: 링 근처에서 짧게
        ang = random.random() * math.tau
        rr = r + random.uniform(-2.0, 2.0)
        x = cx + math.cos(ang) * rr
        y = cy + math.sin(ang) * rr

        # 접선+바깥 성분
        out = random.uniform(70, 110)
        tx = -math.sin(ang)
        ty = math.cos(ang)
        vx = math.cos(ang) * out * 0.35 + tx * out * random.choice([-1, 1]) * 0.65
        vy = math.sin(ang) * out * 0.35 + ty * out * random.choice([-1, 1]) * 0.65

        p = Particle(
            x=x, y=y, vx=vx, vy=vy,
            life=random.uniform(0.35, 0.65),
            age=0.0,
            size=random.uniform(0.8, 1.6),
            seed=random.random() * 999.0,
            warm=random.uniform(0.4, 0.9),
            orbit=0.0,
            pull=0.0,
            kind=1
        )
        self.particles.append(p)

    def burst(self, n: int, where: str, warm: float, orbit_bias: float = 0.0):
        cx, cy, r = self.scene_params()
        for _ in range(n):
            self.spawn_particle(cx, cy, r, where=where, warm=warm, orbit_bias=orbit_bias)

    # ------------------ 업데이트 ------------------
    def alpha_of(self, p: Particle) -> float:
        # 부드러운 fade-out: smoothstep (튀지 않게)
        t = clamp01(p.age / p.life)
        s = t * t * (3.0 - 2.0 * t)
        return clamp01(1.0 - s)

    def update_particle(self, p: Particle, cx: float, cy: float, r: float):
        dt = self.dt
        p.age += dt

        # 난류 드리프트 (코로나 핵심)
        nx, ny = self.flow(self.t + p.seed * 0.01, p.seed)
        drift = 18.0 if p.kind == 0 else 10.0
        p.vx += nx * drift * dt
        p.vy += ny * drift * dt

        # THINK/RESOLVE: 중심 회귀 성향 ("확산되지만 중심을 잃지 않는다")
        if self.state in (self.THINK, self.RESOLVE) and p.kind == 0:
            dx = cx - p.x
            dy = cy - p.y
            d = max(1.0, math.hypot(dx, dy))
            pull_strength = p.pull * 20.0
            p.vx += (dx / d) * pull_strength * dt
            p.vy += (dy / d) * pull_strength * dt

        # WAKE: 일부 궤도 회전
        if self.state == self.WAKE and p.orbit > 0.35 and p.kind == 0:
            dx = p.x - cx
            dy = p.y - cy
            d = max(1.0, math.hypot(dx, dy))
            tx = -dy / d
            ty = dx / d
            orbit_strength = 55.0 * p.orbit
            spin = 1.0 if (p.seed % 2.0) > 1.0 else -1.0
            p.vx += tx * orbit_strength * dt * spin
            p.vy += ty * orbit_strength * dt * spin

        # 위치
        p.x += p.vx * dt
        p.y += p.vy * dt

        # 감쇠: 먼지처럼 느리게 둥둥
        damp = 0.55 if p.kind == 0 else 2.2
        k = math.exp(-damp * dt)
        p.vx *= k
        p.vy *= k

        # 너무 멀리 가면 자연 소멸 유도
        dist = math.hypot(p.x - cx, p.y - cy)
        if dist > r * 4.3:
            p.vx *= 0.90
            p.vy *= 0.90

    # ------------------ 렌더 ------------------
    def draw_background(self, painter: QPainter):
        # 잔상(트레일): 코나/열기 느낌을 살리려면 "완전 지우기"보다 약한 알파로 덮는 게 좋다
        painter.fillRect(self.rect(), QColor(11, 14, 20, 55))

    def draw_ring(self, painter: QPainter, cx: float, cy: float, r: float):
        # 링 스케일
        scale = 1.0
        if self.state == self.IDLE:
            p = math.sin(self.t * self.idle_pulse_speed * math.tau) * self.idle_pulse_amp
            scale = 1.0 + p
        elif self.state == self.WAKE:
            u = clamp01(self.state_t / self.wake_breath_dur)
            breath = math.sin(u * math.pi)
            scale = 1.0 + breath * self.wake_breath_amp
        elif self.state == self.THINK:
            p = math.sin(self.t * 0.55 * math.tau) * 0.012
            scale = 1.0 + p
        elif self.state == self.RESOLVE:
            u = clamp01(self.state_t / 1.0)
            scale = lerp(1.02, 1.0, 1.0 - (1.0 - u) * (1.0 - u))

        rr = r * scale

        # 코로나 글로우(방사형 그라데이션)
        grad = QRadialGradient(QPointF(cx, cy), rr * 2.2)
        grad.setColorAt(0.00, QColor(255, 255, 255, 0))
        grad.setColorAt(0.38, QColor(255, 255, 255, 16))
        grad.setColorAt(0.55, QColor(255, 106, 138, 22))
        grad.setColorAt(0.68, QColor(255, 46, 46, 12))
        grad.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), rr * 1.45, rr * 1.45)

        # 링 자체(얇게 + 약간의 발광)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        pen_glow = QPen(QColor(243, 244, 246, 35), self.ring_thickness * 6.0)
        pen_glow.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_glow)
        painter.drawEllipse(QPointF(cx, cy), rr, rr)

        pen = QPen(QColor(243, 244, 246, 170), self.ring_thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(cx, cy), rr, rr)

        # 아주 약한 코어 점
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(243, 244, 246, 40))
        painter.drawEllipse(QPointF(cx, cy), 2.0, 2.0)

    def draw_particles(self, painter: QPainter):
        # 가산합성: 열복사/코로나 느낌은 이게 거의 필수
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)

        for p in self.particles:
            a = self.alpha_of(p)
            if a <= 0.0:
                continue

            c = self.mix_color(p.warm)
            if p.kind == 0:
                # "먼지" : 아주 작은 핵 + 매우 약한 글로우
                glow_a = int(40 * a)     # 은은
                core_a = int(110 * a)    # 작은 점

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(c.red(), c.green(), c.blue(), glow_a))
                painter.drawEllipse(QPointF(p.x, p.y), p.size * 2.2, p.size * 2.2)

                painter.setBrush(QColor(c.red(), c.green(), c.blue(), core_a))
                painter.drawEllipse(QPointF(p.x, p.y), p.size * 0.9, p.size * 0.9)

            else:
                # 플레어/스파크: 아주 얇은 선분 느낌
                spark_a = int(140 * a)
                pen = QPen(QColor(c.red(), c.green(), c.blue(), spark_a), 1.0)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)

                # 속도 방향으로 짧게 그어줌
                dx = p.vx * 0.02
                dy = p.vy * 0.02
                painter.drawLine(QPointF(p.x - dx, p.y - dy), QPointF(p.x + dx, p.y + dy))

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

    # ------------------ Tick ------------------
    def on_tick(self):
        self.t += self.dt
        self.state_t += self.dt

        cx, cy, r = self.scene_params()

        # 상태별 spawn
        if self.state == self.IDLE:
            rate = self.idle_rate
            warm = 0.12
            where_bias = 0.75  # 대부분 rim
        elif self.state == self.WAKE:
            rate = self.wake_rate
            warm = 0.45
            where_bias = 0.45  # inside가 더 많게
        elif self.state == self.THINK:
            rate = self.think_rate
            warm = 0.22
            where_bias = 0.25  # inside 위주
        else:  # RESOLVE
            rate = self.resolve_rate
            warm = 0.10
            where_bias = 0.85  # 거의 rim만, 그리고 적게

        self.spawn_acc += self.dt * rate
        while self.spawn_acc >= 1.0:
            self.spawn_acc -= 1.0
            where = "rim" if random.random() < where_bias else "inside"
            orbit_bias = 0.75 if self.state == self.WAKE else 0.0
            self.spawn_particle(cx, cy, r, where=where, warm=warm, orbit_bias=orbit_bias)

        # 플레어(가끔)
        self.flare_cooldown -= self.dt
        if self.flare_cooldown <= 0.0:
            if self.state in (self.WAKE, self.THINK) and random.random() < 0.55:
                self.spawn_flare(cx, cy, r)
            # 빈도 제어
            self.flare_cooldown = random.uniform(0.08, 0.22) if self.state == self.THINK else random.uniform(0.14, 0.35)

        # RESOLVE: 파티클 급감(목표치로 정리)
        if self.state == self.RESOLVE:
            self.resolve_kick = clamp01(self.resolve_kick + self.dt * 2.0)
            if len(self.particles) > self.resolve_target:
                # 사망에 가까운 것/오래된 것부터 더 빨리 정리
                self.particles.sort(key=lambda p: (p.age / p.life))
                cut = min(len(self.particles) - self.resolve_target, 18)
                if cut > 0:
                    self.particles = self.particles[cut:]
            else:
                # 안정 복귀
                if self.state_t > 1.4:
                    self.set_state(self.IDLE)

        # 업데이트 + 제거
        alive = []
        for p in self.particles:
            self.update_particle(p, cx, cy, r)
            if p.age < p.life:
                alive.append(p)
        self.particles = alive

        self.update()

    # ------------------ Paint ------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 배경 잔상
        self.draw_background(painter)

        cx, cy, r = self.scene_params()

        # 링(코로나)
        self.draw_ring(painter, cx, cy, r)

        # 파티클(먼지 + 플레어)
        self.draw_particles(painter)

        # 디버그 텍스트(원하면 주석)
        painter.setPen(QColor(255, 255, 255, 90))
        painter.drawText(12, self.height() - 12, f"state={self.state}  particles={len(self.particles)}")

    # ------------------ 키보드로 상태 전환 ------------------
    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_1:
            self.set_state(self.IDLE)
        elif e.key() == Qt.Key.Key_2:
            self.set_state(self.WAKE)
        elif e.key() == Qt.Key.Key_3:
            self.set_state(self.THINK)
        elif e.key() == Qt.Key.Key_4:
            self.set_state(self.RESOLVE)
        else:
            super().keyPressEvent(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ZiTTACoronaWidget()
    w.resize(1000, 700)
    w.show()
    sys.exit(app.exec())
