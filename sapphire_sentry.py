#!/usr/bin/env python3
"""Sapphire Sentry — neon tower-defense lite arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/SAPPHIRE_SENTRY_ElbowOS.mp4")
TITLE, HANDLE = "SAPPHIRE SENTRY", "x.com/ElbowOS"
NAVY = (8, 6, 22)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 180)
GOLD = (255, 215, 0)
ORANGE = (255, 140, 0)
WHITE = (255, 255, 255)
PURPLE = (80, 0, 120)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("dejavusans", 72, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 36, bold=True)
        self.reset()

    def reset(self):
        self.t = 0
        self.score = 0
        self.turrets = []  # (x, y, cooldown)
        self.enemies = []  # (x, y, hp, speed)
        self.shots = []    # (x, y, vx, vy)
        self.particles = []
        self.base_y = H - 180
        self.spawn_timer = 0
        self.place_timer = 0
        random.seed(42)

    def autoplay(self):
        # scripted placement and mild aiming
        self.place_timer += 1
        if self.place_timer > 40 and len(self.turrets) < 5:
            x = 180 + len(self.turrets) * 180
            self.turrets.append([x, self.base_y - 80, 0])
            self.place_timer = 0
        # aim nearest
        for tur in self.turrets:
            tur[2] = max(0, tur[2] - 1)
            if tur[2] <= 0 and self.enemies:
                nearest = min(self.enemies, key=lambda e: math.hypot(e[0]-tur[0], e[1]-tur[1]))
                dx, dy = nearest[0] - tur[0], nearest[1] - tur[1]
                dist = math.hypot(dx, dy) or 1
                spd = 14
                self.shots.append([tur[0], tur[1], dx/dist*spd, dy/dist*spd])
                tur[2] = 12

    def tick(self):
        self.t += 1
        self.spawn_timer += 1
        if self.spawn_timer > 25:
            self.enemies.append([random.randint(100, W-100), -40, 3, 2.5 + random.random()])
            self.spawn_timer = 0
        # move enemies
        for e in self.enemies[:]:
            e[1] += e[3]
            if e[1] > self.base_y:
                self.enemies.remove(e)
                self.score = max(0, self.score - 10)
        # shots
        for s in self.shots[:]:
            s[0] += s[2]; s[1] += s[3]
            if not (0 < s[0] < W and 0 < s[1] < H):
                self.shots.remove(s)
                continue
            for e in self.enemies[:]:
                if math.hypot(s[0]-e[0], s[1]-e[1]) < 36:
                    e[2] -= 1
                    self.shots.remove(s)
                    if e[2] <= 0:
                        self.enemies.remove(e)
                        self.score += 50
                        for _ in range(8):
                            self.particles.append([e[0], e[1], random.uniform(-4,4), random.uniform(-4,4), 20])
                    break
        # particles
        for p in self.particles[:]:
            p[0] += p[2]; p[1] += p[3]; p[4] -= 1
            if p[4] <= 0:
                self.particles.remove(p)

    def draw(self, surf):
        surf.fill(NAVY)
        # stars
        for i in range(60):
            pygame.draw.circle(surf, (40, 30, 70), ((i*137) % W, (i*89 + self.t) % H), 1)
        # base
        pygame.draw.rect(surf, CYAN, (0, self.base_y, W, 8))
        pygame.draw.rect(surf, (0, 100, 120), (0, self.base_y+8, W, H-self.base_y-8))
        # turrets
        for tur in self.turrets:
            pygame.draw.circle(surf, MAGENTA, (int(tur[0]), int(tur[1])), 28)
            pygame.draw.circle(surf, GOLD, (int(tur[0]), int(tur[1])), 12)
        # enemies
        for e in self.enemies:
            pygame.draw.circle(surf, ORANGE, (int(e[0]), int(e[1])), 22)
            pygame.draw.circle(surf, WHITE, (int(e[0]), int(e[1])), 8)
        # shots
        for s in self.shots:
            pygame.draw.circle(surf, CYAN, (int(s[0]), int(s[1])), 6)
        # particles
        for p in self.particles:
            pygame.draw.circle(surf, GOLD, (int(p[0]), int(p[1])), max(1, p[4]//4))
        # overlay
        title = self.font.render(TITLE, True, CYAN)
        surf.blit(title, title.get_rect(center=(W//2, 120)))
        sc = self.small.render(f"SCORE {self.score}", True, GOLD)
        surf.blit(sc, sc.get_rect(center=(W//2, 200)))
        hand = self.small.render(HANDLE, True, MAGENTA)
        surf.blit(hand, hand.get_rect(center=(W//2, H-80)))

    def play_interactive(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.MOUSEBUTTONDOWN and len(self.turrets) < 6:
                    self.turrets.append([ev.pos[0], self.base_y - 80, 0])
            self.autoplay()
            self.tick()
            self.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def record(self):
        frames = FPS * SECS
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-movflags", "+faststart", OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        canvas = pygame.Surface((W, H))
        try:
            for i in range(frames):
                self.autoplay()
                self.tick()
                self.draw(canvas)
                proc.stdin.write(pygame.image.tostring(canvas, "RGB"))
            proc.stdin.close()
            rc = proc.wait()
            err = proc.stderr.read().decode() if proc.stderr else ""
            if rc != 0:
                raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
            print("wrote", OUT)
        finally:
            pygame.quit()

def main():
    g = Game()
    if PLAY and not RECORD:
        g.play_interactive()
    else:
        g.record()

if __name__ == "__main__":
    main()
