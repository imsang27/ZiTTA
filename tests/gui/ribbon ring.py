import math
import random
import sys
from dataclasses import dataclass

from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath
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
    size: float
    seed: float
    warm: float
    kind: int  # 0 dust, 1 spark


class ZiTTARibbonRing(QWidget):
    IDLE = "idle"
    WAKE = "wake"
    THINK = "think"
    RESOLVE = "resolve"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZiTTA Ribbon Ring + Dust (PyQt6)")
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        self.fps = 60
        self.dt = 1.0 / self.fps
        self.t = 0.0
        self.state = self.IDLE
        self.state_t = 0.0

        # ---- 컬러 (보라 계열 + 핑크/레드 입자) ----
        self.bg = QColor(8, 8, 12)                 # 거의 블랙
        
        # ZiTTA ring palette (핑크 80 / 레드 20 + 약한 화이트 하이라이트)
        self.ring_base = QColor(255, 106, 138)     # #FF6A8A (핑크)
        self.ring_deep = QColor(255, 46, 46)       # #FF2E2E (레드)

        # 아주 약한 하이라이트(리본 결이 살아남)
        self.ring_high = QColor(243, 244, 246)     # near-white
        self.pink = QColor(255, 106, 138)          # 입자(핑크)
        self.red = QColor(255, 46, 46)             # 입자(레드)

        # ---- 링 파라미터 ----
        self.ring_ratio = 0.26
        self.idle_pulse_amp = 0.008
        self.idle_pulse_speed = 0.65
        self.wake_breath_amp = 0.045
        self.wake_breath_dur = 1.15

        # 리본 스트랜드(겹수)
        self.strands = 9
        self.points_per_strand = 220

        # 리본 유동(웨이브)
        self.wave_amp = 10.0       # 리본 두께감/요동 크기
        self.wave_freq1 = 2.0
        self.wave_freq2 = 3.4
        self.flow_speed = 0.55     # 링을 따라 흐르는 속도

        # ---- 파티클 ----
        self.particles: list[Particle] = []
        self.max_particles = 1600
        self.resolve_target = 140
        self.spawn_acc = 0.0
        self.resolve_kick = 0.0
        self.flare_cd = 0.0

        # 상태별 스폰 레이트
        self.idle_rate = 70
        self.wake_rate = 150
        self.think_rate = 210
        self.resolve_rate = 6

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)
        self.timer.start(int(1000 / self.fps))

        self.seed_initial()

    # ---------------- State ----------------
    def set_state(self, s: str):
        if s not in (self.IDLE, self.WAKE, self.THINK, self.RESOLVE):
            return
        self.state = s
        self.state_t = 0.0

        if s == self.WAKE:
            self.burst(140, warm=0.25, bias_out=0.25)
        if s == self.RESOLVE:
            self.resolve_kick = 1.0

    # ---------------- Scene ----------------
    def scene(self):
        w = max(1, self.width())
        h = max(1, self.height())
        cx = w * 0.5
        cy = h * 0.5
        r = min(w, h) * self.ring_ratio
        return w, h, cx, cy, r

    # ---------------- Helpers ----------------
    def flow_noise(self, t: float, seed: float):
        # 부드러운 유동 노이즈(리본/입자에 사용)
        x = math.sin(t * 1.8 + seed * 11.1) * 0.65 + math.sin(t * 0.9 + seed * 3.3) * 0.35
        y = math.cos(t * 1.4 + seed * 7.7) * 0.65 + math.cos(t * 0.8 + seed * 5.5) * 0.35
        return x, y

    def mix_particle_color(self, warm: float) -> QColor:
        warm = clamp01(warm)
        r = int(lerp(self.pink.red(), self.red.red(), warm))
        g = int(lerp(self.pink.green(), self.red.green(), warm))
        b = int(lerp(self.pink.blue(), self.red.blue(), warm))
        return QColor(r, g, b)

    def alpha_smooth(self, p: Particle) -> float:
        t = clamp01(p.age / p.life)
        s = t * t * (3.0 - 2.0 * t)  # smoothstep
        return clamp01(1.0 - s)

    # ---------------- Particle spawn ----------------
    def seed_initial(self):
        _, _, cx, cy, r = self.scene()
        for _ in range(650):
            self.spawn_from_ring(cx, cy, r, warm=0.10, bias_out=0.18)

    def spawn_from_ring(self, cx, cy, r, warm: float, bias_out: float):
        # "리본 링 위에서 새어나오듯" 방출: 각도 기반으로 링 좌표를 잡는다
        ang = random.random() * math.tau

        # 링의 리본 변형을 반영해서 좌표를 살짝 흔든다
        wob = self.ribbon_radius_offset(ang, strand_seed=random.random() * 10.0)
        rr = r + wob

        x = cx + math.cos(ang) * rr
        y = cy + math.sin(ang) * rr

        # 속도: 기본은 '접선 방향 흐름' + 약한 outward + 난류
        tx = -math.sin(ang)
        ty = math.cos(ang)

        # 상태별: THINK에서 더 확산, IDLE은 얌전
        base_tan = 22 if self.state != self.IDLE else 16
        base_out = 10 if self.state == self.THINK else 6

        # “흘러나온다”를 만들려면 접선이 주역이고 outward는 보조여야 한다
        vx = tx * base_tan + math.cos(ang) * (base_out * bias_out) + random.uniform(-2, 2)
        vy = ty * base_tan + math.sin(ang) * (base_out * bias_out) + random.uniform(-2, 2)

        # 난류
        nx, ny = self.flow_noise(self.t + ang, random.random() * 999)
        vx += nx * 10
        vy += ny * 10

        p = Particle(
            x=x, y=y,
            vx=vx, vy=vy,
            life=random.uniform(2.4, 5.2),
            age=0.0,
            size=random.uniform(0.35, 1.05),  # 먼지처럼 작게
            seed=random.random() * 999.0,
            warm=warm,
            kind=0
        )
        self.particles.append(p)

        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]

    def spawn_spark(self, cx, cy, r):
        # 가끔 있는 "별빛 점멸/스파크"
        ang = random.random() * math.tau
        rr = r + self.ribbon_radius_offset(ang, strand_seed=7.7) * 0.9
        x = cx + math.cos(ang) * rr
        y = cy + math.sin(ang) * rr

        tx = -math.sin(ang)
        ty = math.cos(ang)

        speed = random.uniform(80, 120)
        vx = tx * speed * random.choice([-1, 1]) * 0.8 + math.cos(ang) * speed * 0.2
        vy = ty * speed * random.choice([-1, 1]) * 0.8 + math.sin(ang) * speed * 0.2

        p = Particle(
            x=x, y=y,
            vx=vx, vy=vy,
            life=random.uniform(0.20, 0.45),
            age=0.0,
            size=random.uniform(0.7, 1.5),
            seed=random.random() * 999.0,
            warm=random.uniform(0.05, 0.35),
            kind=1
        )
        self.particles.append(p)

    def burst(self, n: int, warm: float, bias_out: float):
        _, _, cx, cy, r = self.scene()
        for _ in range(n):
            self.spawn_from_ring(cx, cy, r, warm=warm, bias_out=bias_out)

    # ---------------- Ribbon ring geometry ----------------
    def ribbon_radius_offset(self, ang: float, strand_seed: float):
        # 이미지처럼 "리본이 겹치며 흐르는 느낌"은
        # 각도에 따른 반경 오프셋 + 시간에 따른 phase drift로 만든다.
        # (연속성이 중요: sin/cos로 충분히 자연스럽게 나온다)
        t = self.t * self.flow_speed
        a1 = math.sin(ang * self.wave_freq1 + t * 2.0 + strand_seed * 1.3)
        a2 = math.sin(ang * self.wave_freq2 - t * 1.4 + strand_seed * 2.1)
        return (a1 * 0.65 + a2 * 0.35) * self.wave_amp

    def ring_scale(self):
        # 상태별 링 스케일(Idle pulse, Wake breath)
        if self.state == self.IDLE:
            p = math.sin(self.t * self.idle_pulse_speed * math.tau) * self.idle_pulse_amp
            return 1.0 + p
        if self.state == self.WAKE:
            u = clamp01(self.state_t / self.wake_breath_dur)
            breath = math.sin(u * math.pi)
            return 1.0 + breath * self.wake_breath_amp
        if self.state == self.THINK:
            p = math.sin(self.t * 0.50 * math.tau) * 0.012
            return 1.0 + p
        # RESOLVE
        u = clamp01(self.state_t / 1.0)
        return lerp(1.02, 1.0, 1.0 - (1.0 - u) * (1.0 - u))

    # ---------------- Update ----------------
    def on_tick(self):
        self.t += self.dt
        self.state_t += self.dt

        _, _, cx, cy, r = self.scene()

        # 상태별 스폰
        if self.state == self.IDLE:
            rate = self.idle_rate
            warm = 0.08
            bias_out = 0.18
        elif self.state == self.WAKE:
            rate = self.wake_rate
            warm = 0.18
            bias_out = 0.30
        elif self.state == self.THINK:
            rate = self.think_rate
            warm = 0.12
            bias_out = 0.40
        else:
            rate = self.resolve_rate
            warm = 0.06
            bias_out = 0.10

        self.spawn_acc += self.dt * rate
        while self.spawn_acc >= 1.0:
            self.spawn_acc -= 1.0
            self.spawn_from_ring(cx, cy, r, warm=warm, bias_out=bias_out)

        # 스파크 (절제된 플레어)
        self.flare_cd -= self.dt
        if self.flare_cd <= 0.0:
            if self.state in (self.WAKE, self.THINK) and random.random() < 0.35:
                self.spawn_spark(cx, cy, r)
            self.flare_cd = random.uniform(0.10, 0.28) if self.state == self.THINK else random.uniform(0.18, 0.45)

        # RESOLVE: 급감
        if self.state == self.RESOLVE:
            self.resolve_kick = clamp01(self.resolve_kick + self.dt * 2.0)
            if len(self.particles) > self.resolve_target:
                self.particles.sort(key=lambda p: (p.age / p.life))
                cut = min(len(self.particles) - self.resolve_target, 22)
                if cut > 0:
                    self.particles = self.particles[cut:]
            else:
                if self.state_t > 1.3:
                    self.set_state(self.IDLE)
        else:
            self.resolve_kick = 0.0

        # 파티클 업데이트
        alive = []
        for p in self.particles:
            p.age += self.dt

            # 난류로 곡선 운동
            nx, ny = self.flow_noise(self.t + p.seed * 0.01, p.seed)
            drift = 16.0 if p.kind == 0 else 9.0
            p.vx += nx * drift * self.dt
            p.vy += ny * drift * self.dt

            # THINK: 일부는 중심 회귀(“중심을 잃지 않는다”)
            if self.state in (self.THINK, self.RESOLVE) and p.kind == 0:
                dx = cx - p.x
                dy = cy - p.y
                d = max(1.0, math.hypot(dx, dy))
                pull = 12.0
                p.vx += (dx / d) * pull * self.dt
                p.vy += (dy / d) * pull * self.dt

            # 위치
            p.x += p.vx * self.dt
            p.y += p.vy * self.dt

            # 감쇠(먼지 느낌)
            damp = 0.75 if p.kind == 0 else 2.4
            k = math.exp(-damp * self.dt)
            p.vx *= k
            p.vy *= k

            # 너무 멀면 자연 소멸 유도
            dist = math.hypot(p.x - cx, p.y - cy)
            if dist > r * 4.6:
                p.vx *= 0.90
                p.vy *= 0.90

            if p.age < p.life:
                alive.append(p)

        self.particles = alive
        self.update()

    # ---------------- Paint ----------------
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w, h, cx, cy, r = self.scene()

        # 잔상(리본 흐름 강조)
        painter.fillRect(self.rect(), QColor(self.bg.red(), self.bg.green(), self.bg.blue(), 55))

        # 링(리본): 가산합성으로 "광학적으로 쌓이는" 느낌
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        self.draw_ribbon_ring(painter, cx, cy, r)
        self.draw_particles(painter)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # 디버그 텍스트(필요 없으면 삭제)
        painter.setPen(QColor(255, 255, 255, 80))
        painter.drawText(12, h - 12, f"state={self.state}  particles={len(self.particles)}   (1-4 키로 상태 전환)")

    def draw_ribbon_ring(self, painter: QPainter, cx: float, cy: float, r: float):
        scale = self.ring_scale()
        state_warm = 0.0 if self.state == self.IDLE else (0.10 if self.state == self.WAKE else 0.06)
        rr = r * scale

        # 여러 스트랜드(얇은 실선들이 겹쳐서 "리본 베일"이 된다)
        for s in range(self.strands):
            seed = (s + 1) * 1.37
            path = QPainterPath()

            # 스트랜드마다 두께/투명도/색을 다르게 해서 깊이를 만든다
            # (겹치면 밝아지는 건 Plus 합성으로 해결)
            depth = s / max(1, self.strands - 1)
            # 바깥/안쪽이 교차하는 느낌
            local_amp = self.wave_amp * lerp(0.55, 1.05, math.sin(self.t * 0.6 + seed) * 0.5 + 0.5)

            # ZiTTA 비율: 핑크(0.8) 기반 + 레드(0.2) 기여 + 깊이에 따른 변주
            # depth가 깊어질수록(안쪽/어두운 스트랜드) 레드 비중이 약간 증가하도록 설계
            pink = self.ring_base
            red = self.ring_deep
            white = self.ring_high

            red_mix = (0.18 + 0.22 * depth) + state_warm
            red_mix = clamp01(red_mix)
            pink_mix = 1.0 - red_mix

            # base mix (pink-red)
            br = int(pink.red()   * pink_mix + red.red()   * red_mix)
            bg = int(pink.green() * pink_mix + red.green() * red_mix)
            bb = int(pink.blue()  * pink_mix + red.blue()  * red_mix)

            # 아주 약한 화이트 하이라이트(깊이가 얕을수록 조금 더)
            hi = 0.08 * (1.0 - depth)              # 0~0.08
            cr = int(br * (1.0 - hi) + white.red()   * hi)
            cg = int(bg * (1.0 - hi) + white.green() * hi)
            cb = int(bb * (1.0 - hi) + white.blue()  * hi)

            alpha = int(lerp(14, 42, (1 - depth)))  # 얇고 여러 겹이라 알파는 낮게
            col = QColor(cr, cg, cb, alpha)

            width = lerp(0.8, 1.8, (1 - depth))

            pen = QPen(col, width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)

            # 링을 따라 점들을 찍어 path 구성
            first = True
            for i in range(self.points_per_strand + 1):
                u = i / self.points_per_strand
                ang = u * math.tau

                # 스트랜드마다 phase가 달라 "흐름"이 생김
                phase = self.t * self.flow_speed * 1.7 + seed * 0.9
                wob = (
                    math.sin(ang * self.wave_freq1 + phase) * 0.65
                    + math.sin(ang * self.wave_freq2 - phase * 0.9) * 0.35
                ) * local_amp

                # 얇은 리본이 겹치는 느낌: 스트랜드별로 약간의 편차
                wob += math.sin(ang * 1.2 + seed * 2.1) * 2.0

                rad = rr + wob

                x = cx + math.cos(ang) * rad
                y = cy + math.sin(ang) * rad

                if first:
                    path.moveTo(QPointF(x, y))
                    first = False
                else:
                    path.lineTo(QPointF(x, y))

            painter.drawPath(path)

        # 링 중심선(아주 약하게) — "원형 코어"
        # 코어 원: 핑크 계열의 아주 약한 잔광
        painter.setPen(QPen(QColor(255, 106, 138, 18), 1.2))
        painter.drawEllipse(QPointF(cx, cy), rr, rr)

    def draw_particles(self, painter: QPainter):
        # 이미 Plus 합성 상태에서 호출됨
        for p in self.particles:
            a = self.alpha_smooth(p)
            if a <= 0:
                continue

            if p.kind == 0:
                c = self.mix_particle_color(p.warm)
                # 별가루: 아주 작은 점 + 약한 글로우
                glow_a = int(26 * a)
                core_a = int(110 * a)

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(c.red(), c.green(), c.blue(), glow_a))
                painter.drawEllipse(QPointF(p.x, p.y), p.size * 2.0, p.size * 2.0)

                painter.setBrush(QColor(c.red(), c.green(), c.blue(), core_a))
                painter.drawEllipse(QPointF(p.x, p.y), p.size * 0.85, p.size * 0.85)
            else:
                # 스파크: 짧은 선
                c = self.mix_particle_color(p.warm)
                pen = QPen(QColor(c.red(), c.green(), c.blue(), int(150 * a)), 1.0)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                dx = p.vx * 0.02
                dy = p.vy * 0.02
                painter.drawLine(QPointF(p.x - dx, p.y - dy), QPointF(p.x + dx, p.y + dy))

    # ---------------- Keyboard ----------------
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
    w = ZiTTARibbonRing()
    w.resize(1000, 750)
    w.show()
    sys.exit(app.exec())
