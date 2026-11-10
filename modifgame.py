import tkinter as tk
import random

# ==========================================
# KONFIGURASI TEMA CYBERPUNK (PALET WARNA)
# ==========================================
BG_COLOR = '#0d0e15'          # Gelap pekat (Latar belakang)
COLOR_CYAN = '#00FFFF'        # Cyan Neon
COLOR_MAGENTA = '#FF00FF'     # Magenta Neon
COLOR_GREEN = '#39FF14'       # Hijau Neon
COLOR_YELLOW = '#FFFF00'      # Kuning Neon
COLOR_RED = '#FF3131'         # Merah Neon (Bahaya/Tantangan)
FONT_DIGITAL = ('Consolas', 14, 'bold') # Font bergaya digital/koding

# ==========================================
# KELAS DASAR (BASE CLASS)
# ==========================================
class GameObject(object):
    """
    Kelas dasar untuk semua objek di dalam game (Bola, Paddle, Bata, dll).
    Mengatur posisi, pergerakan dasar, dan penghapusan objek dari Canvas.
    """
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        # Mengembalikan koordinat objek [x1, y1, x2, y2]
        return self.canvas.coords(self.item)

    def move(self, x, y):
        # Memindahkan objek sejauh x (horizontal) dan y (vertikal)
        self.canvas.move(self.item, x, y)

    def delete(self):
        # Menghapus objek dari layar (canvas)
        self.canvas.delete(self.item)

    def get_center(self):
        # Menghitung titik tengah objek berdasarkan koordinatnya
        coords = self.get_position()
        return (coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2


# ==========================================
# KELAS BOLA (BALL)
# ==========================================
class Ball(GameObject):
    """
    Mengontrol bola yang memantul. Memiliki kecepatan yang bisa diubah (efek level/powerup).
    """
    def __init__(self, canvas, x, y, base_speed=6):
        self.radius = 8
        self.direction = [1, -1] # Awal bergerak ke kanan (1) dan atas (-1)
        self.base_speed = base_speed
        self.speed = base_speed
        
        # Membuat bola bercahaya (warna cyan dengan outline putih)
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill=COLOR_CYAN, outline='white', width=2)
        super(Ball, self).__init__(canvas, item)

    def update(self):
        """Menggerakkan bola dan memantulkannya jika mengenai dinding."""
        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        # Pantulan kiri/kanan
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
            
        # Pantulan atas
        if coords[1] <= 0:
            self.direction[1] *= -1
            
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        """
        Menangani logika tabrakan bola dengan objek lain (Paddle / Bata).
        """
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5 # Titik tengah bola (sumbu x)
        
        # Jika menabrak lebih dari satu objek, pantulkan ke bawah/atas
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            obj_coords = game_object.get_position()
            
            # Logika pantulan cerdas berdasarkan posisi bola mengenai objek
            if x > obj_coords[2]:
                self.direction[0] = 1   # Pantul ke kanan
            elif x < obj_coords[0]:
                self.direction[0] = -1  # Pantul ke kiri
            else:
                self.direction[1] *= -1 # Pantul secara vertikal

        # Jika objek yang ditabrak adalah bata, panggil fungsi hit() pada bata tersebut
        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


# ==========================================
# KELAS PADDLE (PAPAN PEMAIN)
# ==========================================
class Paddle(GameObject):
    """
    Papan pemain yang digerakkan menggunakan panah Kiri/Kanan.
    Ukurannya bisa memanjang jika mendapat power-up 'Expand'.
    """
    def __init__(self, canvas, x, y):
        self.default_width = 80
        self.width = self.default_width
        self.height = 12
        self.ball = None
        
        # Desain paddle dengan warna hijau neon
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=COLOR_GREEN, outline='white', width=2)
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        """Menggerakkan paddle tanpa melewati batas layar."""
        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        # Cek apakah gerakan masih di dalam layar
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            # Jika bola masih menempel di paddle (sebelum game mulai), gerakkan bola juga
            if self.ball is not None:
                self.ball.move(offset, 0)

    def change_width(self, new_width):
        """Mengubah ukuran paddle (efek power-up)."""
        self.width = new_width
        coords = self.get_position()
        x_center = (coords[0] + coords[2]) / 2
        y_center = (coords[1] + coords[3]) / 2
        
        # Menggambar ulang ukuran di canvas
        self.canvas.coords(self.item, 
                           x_center - self.width / 2, y_center - self.height / 2,
                           x_center + self.width / 2, y_center + self.height / 2)


# ==========================================
# KELAS BRICK (BATA)
# ==========================================
class Brick(GameObject):
    """
    Bata yang harus dihancurkan. Memiliki nyawa (hits) dan warna yang berbeda.
    """
    # Warna berdasarkan jumlah hits tersisa (Cyberpunk theme)
    COLORS = {1: COLOR_MAGENTA, 2: COLOR_CYAN, 3: COLOR_YELLOW}

    def __init__(self, canvas, x, y, hits, game_instance):
        self.width = 65
        self.height = 20
        self.hits = hits
        self.game = game_instance # Menyimpan referensi game untuk menambah skor / spawn powerup
        color = Brick.COLORS[hits]
        
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, outline=BG_COLOR, width=2, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        """Dipanggil saat bola menabrak bata ini."""
        self.hits -= 1
        self.game.add_score(10) # Tambah 10 poin setiap hit
        
        # EFEK VISUAL: Flicker / Kedip putih sebentar sebelum ganti warna atau hancur
        self.canvas.itemconfig(self.item, fill='white')
        
        if self.hits == 0:
            # Menggunakan timer after agar sempat terlihat putih sebelum hilang
            self.canvas.after(50, self.destroy_brick)
        else:
            self.canvas.after(50, lambda: self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits]))

    def destroy_brick(self):
        """Menghapus bata dan mengacak probabilitas jatuhnya power-up."""
        coords = self.get_position()
        x_center = (coords[0] + coords[2]) / 2
        y_center = (coords[1] + coords[3]) / 2
        self.delete()
        
        # Peluang 25% bata akan menjatuhkan Power-Up
        if random.random() < 0.25:
            self.game.spawn_powerup(x_center, y_center)


# ==========================================
# KELAS POWER-UP & LASER
# ==========================================
class PowerUp(GameObject):
    """Kapsul power-up yang jatuh ke bawah."""
    TYPES = ['expand', 'laser', 'fast']
    COLORS = {'expand': COLOR_CYAN, 'laser': COLOR_MAGENTA, 'fast': COLOR_RED}

    def __init__(self, canvas, x, y):
        self.type = random.choice(self.TYPES) # Pilih tipe secara acak
        self.radius = 8
        color = self.COLORS[self.type]
        
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill=color, outline='white', tags='powerup')
        super(PowerUp, self).__init__(canvas, item)

    def update(self):
        """Powerup jatuh perlahan ke bawah."""
        self.move(0, 3) # Jatuh 3 piksel per frame


class Laser(GameObject):
    """Proyektil yang ditembakkan oleh paddle saat mendapat powerup 'Laser'."""
    def __init__(self, canvas, x, y):
        item = canvas.create_rectangle(x - 2, y - 10, x + 2, y, fill=COLOR_MAGENTA, tags='laser')
        super(Laser, self).__init__(canvas, item)

    def update(self):
        """Laser bergerak lurus ke atas."""
        self.move(0, -7) # Bergerak ke atas (sumbu Y negatif)


# ==========================================
# KELAS UTAMA: GAME ENGINE
# ==========================================
class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.score = 0
        self.level = 1
        self.width = 640
        self.height = 480
        
        # Membuat Canvas (Layar Game)
        self.canvas = tk.Canvas(self, bg=BG_COLOR,
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        # Struktur Data Penyimpanan Objek
        self.items = {}      # Menyimpan bata
        self.powerups = []   # Menyimpan powerup aktif di layar
        self.lasers = []     # Menyimpan proyektil laser aktif
        
        self.ball = None
        # Membuat Paddle di tengah bawah
        self.paddle = Paddle(self.canvas, self.width/2, self.height - 40)
        self.items[self.paddle.item] = self.paddle
        
        self.hud_lives = None
        self.hud_score = None
        self.hud_level = None
        
        # Status Power Up
        self.powerup_timers = {'expand': 0, 'laser': 0, 'fast': 0}
        self.laser_cooldown = 0
        
        self.setup_level()
        self.setup_hud()
        
        self.canvas.focus_set()
        
        # Binding Kontrol Keyboard (Kiri/Kanan)
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-25))
        self.canvas.bind('<Right>', lambda _: self.paddle.move(25))

    def setup_level(self):
        """Membuat/Me-reset barisan bata untuk level saat ini."""
        # Hapus bata sisa (jika ada)
        for item_id in self.canvas.find_withtag('brick'):
            if item_id in self.items:
                del self.items[item_id]
            self.canvas.delete(item_id)
            
        # Menyusun bata berbentuk Grid (Tingkat ketahanan bata ditentukan level)
        row_colors = [min(3, self.level + 1), min(2, self.level), 1] # Ketahanan
        y_offset = 60
        for row in range(3):
            hits = row_colors[row]
            for x in range(10, self.width - 70, 70):
                self.add_brick(x + 35, y_offset, max(1, hits))
            y_offset += 25
            
        self.setup_game_state()

    def setup_game_state(self):
        """Menyiapkan bola dan status untuk mulai/melanjutkan permainan."""
        self.add_ball()
        self.update_hud()
        self.text = self.draw_text(self.width/2, self.height/2,
                                   'TEKAN SPASI UNTUK MULAI', size=16, color=COLOR_CYAN)
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        """Meletakkan bola di atas paddle."""
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        
        # Semakin tinggi level, bola semakin cepat
        new_speed = 6 + (self.level - 1) * 1.5
        self.ball = Ball(self.canvas, x, paddle_coords[1] - 15, base_speed=new_speed)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        """Mendaftarkan bata baru ke dictionary self.items."""
        brick = Brick(self.canvas, x, y, hits, self)
        self.items[brick.item] = brick

    def spawn_powerup(self, x, y):
        """Memunculkan objek powerup."""
        p = PowerUp(self.canvas, x, y)
        self.powerups.append(p)

    def draw_text(self, x, y, text, size=14, color='white'):
        """Fungsi pembantu untuk menggambar teks di layar."""
        font = ('Consolas', size, 'bold')
        return self.canvas.create_text(x, y, text=text, font=font, fill=color)

    def setup_hud(self):
        """Membuat teks Heads-Up Display (Nyawa, Skor, Level)."""
        self.hud_lives = self.draw_text(50, 20, f'LIVES: {self.lives}', color=COLOR_RED)
        self.hud_score = self.draw_text(self.width/2, 20, f'SCORE: {self.score}', color=COLOR_CYAN)
        self.hud_level = self.draw_text(self.width - 60, 20, f'LEVEL: {self.level}', color=COLOR_YELLOW)

    def update_hud(self):
        """Memperbarui teks layar secara dinamis."""
        self.canvas.itemconfig(self.hud_lives, text=f'LIVES: {self.lives}')
        self.canvas.itemconfig(self.hud_score, text=f'SCORE: {self.score}')
        self.canvas.itemconfig(self.hud_level, text=f'LEVEL: {self.level}')

    def add_score(self, points):
        """Menambah poin dan mengupdate layar."""
        self.score += points
        self.update_hud()

    def start_game(self):
        """Memicu dimulainya physics bola."""
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None # Melepas bola dari paddle
        self.game_loop()

    def handle_powerups(self):
        """Menangani pergerakan dan tabrakan powerup dengan paddle."""
        paddle_coords = self.paddle.get_position()
        
        for p in self.powerups[:]: # Iterasi copy list agar aman saat dihapus
            p.update()
            coords = p.get_position()
            
            # Jika keluar layar bawah, hapus
            if coords[1] >= self.height:
                p.delete()
                self.powerups.remove(p)
                continue
                
            # Cek Tabrakan dengan Paddle
            items_overlap = self.canvas.find_overlapping(*coords)
            if self.paddle.item in items_overlap:
                self.activate_powerup(p.type)
                p.delete()
                self.powerups.remove(p)

    def activate_powerup(self, ptype):
        """Memicu efek power-up dan mereset timer."""
        # Efek berlangsung selama ~300 frame (sekitar 10 detik di 33ms)
        self.powerup_timers[ptype] = 300 
        
        if ptype == 'expand':
            self.paddle.change_width(self.paddle.default_width + 60)
        elif ptype == 'fast':
            # Tantangan: Kecepatan bertambah drastis
            self.ball.speed = self.ball.base_speed + 4

    def update_powerup_timers(self):
        """Mengurangi durasi timer powerup dan menonaktifkannya jika habis."""
        for ptype in self.powerup_timers:
            if self.powerup_timers[ptype] > 0:
                self.powerup_timers[ptype] -= 1
                
                # Jika timer baru saja habis (menjadi 0)
                if self.powerup_timers[ptype] == 0:
                    if ptype == 'expand':
                        self.paddle.change_width(self.paddle.default_width)
                    elif ptype == 'fast':
                        self.ball.speed = self.ball.base_speed
        
        # Logika menembak otomatis jika powerup 'laser' aktif
        if self.powerup_timers['laser'] > 0:
            self.laser_cooldown -= 1
            if self.laser_cooldown <= 0:
                self.shoot_laser()
                self.laser_cooldown = 15 # Tembak setiap 15 frame (setengah detik)

    def shoot_laser(self):
        """Membuat objek proyektil laser dari kedua ujung paddle."""
        coords = self.paddle.get_position()
        x1 = coords[0] + 10 # Ujung kiri paddle
        x2 = coords[2] - 10 # Ujung kanan paddle
        y = coords[1]
        self.lasers.append(Laser(self.canvas, x1, y))
        self.lasers.append(Laser(self.canvas, x2, y))

    def handle_lasers(self):
        """Mengerakkan laser dan mengecek apakah laser mengenai bata."""
        for laser in self.lasers[:]:
            laser.update()
            coords = laser.get_position()
            
            # Jika keluar layar atas, hapus
            if coords[3] <= 0:
                laser.delete()
                self.lasers.remove(laser)
                continue
                
            # Cek Tabrakan Laser dengan Bata
            items_overlap = self.canvas.find_overlapping(*coords)
            hit_brick = False
            for item in items_overlap:
                if item in self.items and isinstance(self.items[item], Brick):
                    self.items[item].hit()
                    hit_brick = True
                    break # Laser hancur setelah mengenai 1 bata
                    
            if hit_brick:
                laser.delete()
                self.lasers.remove(laser)

    def game_loop(self):
        """Main Loop: Berjalan secara rekursif setiap frame (33ms)."""
        self.check_collisions()
        self.handle_powerups()
        self.handle_lasers()
        self.update_powerup_timers()
        
        # Mengecek apakah masih ada bata tersisa
        num_bricks = len(self.canvas.find_withtag('brick'))
        
        if num_bricks == 0: 
            # Menang (Naik Level)
            self.ball.speed = 0
            self.level += 1
            # Bersihkan objek sisa
            for p in self.powerups: p.delete()
            for l in self.lasers: l.delete()
            self.powerups = []
            self.lasers = []
            self.text = self.draw_text(self.width/2, self.height/2, 'LEVEL CLEAR! MEMUAT...', color=COLOR_GREEN)
            self.after(2000, self.next_level)
            
        elif self.ball.get_position()[3] >= self.height: 
            # Bola Jatuh / Kalah 1 Nyawa
            self.ball.speed = 0
            self.lives -= 1
            self.update_hud()
            
            # Matikan efek powerup
            for ptype in self.powerup_timers:
                self.powerup_timers[ptype] = 0
            self.paddle.change_width(self.paddle.default_width)
            
            if self.lives <= 0:
                self.draw_text(self.width/2, self.height/2, 'GAME OVER!', size=24, color=COLOR_RED)
            else:
                self.after(1000, self.setup_game_state)
        else:
            # Perbarui posisi bola dan panggil loop ini lagi
            self.ball.update()
            self.after(33, self.game_loop) # Menjalankan game pada ~30 FPS

    def next_level(self):
        """Membersihkan teks dan memuat susunan bata untuk level berikutnya."""
        self.canvas.delete(self.text)
        self.setup_level()

    def check_collisions(self):
        """Deteksi objek apa saja yang bersentuhan (overlapping) dengan area bola."""
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        
        # Ambil objek dari dictionary jika ada yang tertabrak
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)


# ==========================================
# INISIALISASI APLIKASI
# ==========================================
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Cyberpunk Brick Breaker')
    root.resizable(False, False) # Ukuran window tidak bisa diubah
    
    # Mengatur background window utama menyesuaikan tema gelap
    root.configure(bg=BG_COLOR)
    
    game = Game(root)
    game.mainloop()