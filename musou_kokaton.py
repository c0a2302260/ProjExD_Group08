import math
import os
import random
import sys
import time
import pygame as pg


WIDTH, HEIGHT = 1600, 900  # ゲームウィンドウの幅，高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct:pg.Rect) -> tuple[bool, bool]:
    """
    Rectの画面内外判定用の関数
    引数：こうかとんRect，または，爆弾Rect，またはビームRect
    戻り値：横方向判定結果，縦方向判定結果（True：画面内／False：画面外）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:  # 横方向のはみ出し判定
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int], state: str, hyper_life: int):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        引数3 state:こうかとんの状態（通常orハイパー）
        引数4 hyper_life:ハイパー状態の持続時間
        """
        self.state = "normal"
        self.hyper_life = 0
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.life = 3  # 自機の残機

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)
            self.hyper_life -= 1
            if self.hyper_life < 0:
                self.state = "normal"
        if key_lst[pg.K_LSHIFT]:
            self.speed = 20
        else:
            self.speed = 10
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.state = "active"
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0: float):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle+angle0, 2.0)
        self.vx = math.cos(math.radians(angle+angle0))
        self.vy = -math.sin(math.radians(angle+angle0))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 30

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Neobeam:
    """
    一度に複数方向へビームを発射することに関するクラス
    """
    def __init__(self, bird: Bird, num: int):
        self.bird = bird
        self.num = num

    def gen_beams(self) -> list:
        angles = [i for i in range(-50, +51, 100//(self.num-1))]  # 同時に発射するビーム全ての角度を格納したリスト
        neobeams = []  # Beamインスタンスを入れるための空のリスト
        for angle in angles:
            neobeams.append(Beam(self.bird, angle))
        return neobeams


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    def __init__(self):
        super().__init__()
        self.tick = random.randint(0, 30)
        self.image = pg.transform.rotozoom(pg.image.load("fig/3_black.png"), 0, 2)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH+10, random.randint(0, HEIGHT)
        self.vx = -6
        self.vy = 0
        self.bound = random.randint(WIDTH*3/4, WIDTH-50)  # 停止位置
        self.state = "setting"  # 準備状態 or 通常状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vxに基づき移動させる
        ランダムに決めた停止位置_boundまで移動したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        self.tick += 1
        self.vy *= 0.95

        if self.state == "setting" and self.rect.centerx < self.bound:
            self.vx = -1
            self.state = "normal"

        if self.state == "normal":
            if self.tick % 100 == 0:
                self.vy = random.choice([-10, 10])

        if not 0 < self.rect.centery + self.vy <HEIGHT:
            self.vy *= -1
        self.rect.move_ip(self.vx, self.vy)


class Wave:
    """
    ウェーブと敵のスポーンを管理して、UIを表示するクラス
    """
    def __init__(self, wave: int):
        """
        新しいWaveを生成する
        引数 wave:生成するWaveのレベルを指定する
        """
        self.wave = wave
        self.max_enemies = 1 + 2 * wave  #画面に存在する敵の最大数
        self.interval = 200 / wave  #次の敵が出るまでの最短時間
        self.killcount = 0  #現在のウェーブでのキル数
        self.finish_killcount = 10 * wave  #現在のウェーブでの目標キル数
        self.latest_spawn = 0  #前回敵が出てからのフレーム数
        self.tick = 0  #このWaveが生成されてからのフレーム数

        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.ui = self.font.render(f"wave: {wave} enemies: {self.finish_killcount}", 0, self.color)
        self.ui_rct = self.ui.get_rect()
        self.ui_rct.center = 200, 50

        self.black_screen = pg.Surface((WIDTH, HEIGHT))
        self.black_screen.set_alpha(100)
        self.black_screen.fill((0, 0, 0))

        self.title_font = pg.font.Font(None, 200)
        self.wave_title = self.title_font.render(f"WAVE{wave}", 0, (255, 255, 255))
        self.wave_title_rct = self.wave_title.get_rect()
        self.wave_title_rct.center = WIDTH/2, HEIGHT/2

    def update(self, screen: pg.Surface):
        """
        現在のweve数、残りの敵の数を表示するUIを描画する
        引数 screen:画面Surface
        """
        self.latest_spawn += 1
        self.tick += 1
        self.ui = self.font.render(f"wave: {self.wave} enemies: {self.finish_killcount-self.killcount}", 0, self.color)
        screen.blit(self.ui, self.ui_rct)
        if self.tick < 60:
            screen.blit(self.black_screen, [0, 0])
            screen.blit(self.wave_title, self.wave_title_rct)

    def get_enemy_spawn(self, enemy_count: int) -> bool:
        """
        現在敵をスポーンさせることができるかを返す関数
        引数 enemy_count:現在の敵の数
        戻り値 スポーンが可能かどうかのbool
        """
        if enemy_count < self.max_enemies and self.latest_spawn >= self.interval:
            self.latest_spawn = 0
            return True


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class Gravity(pg.sprite.Sprite):
    def __init__(self,life,) -> None:
        super().__init__()
        self.life=life
        self.gra_rct=pg.Surface((WIDTH,HEIGHT))
        pg.draw.rect(self.gra_rct,(0,0,0),(0,0,WIDTH,HEIGHT))
        self.gra_rct.set_alpha(192)
        self.rect=self.gra_rct.get_rect()

    
    def update(self,screen:pg.Surface):
        screen.blit(self.gra_rct,[0,0])
        self.life-=1
        if self.life<0:
            self.kill()
        

class Emp:
    """
    EMP
    """
    def __init__(self, emys: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.Surface):
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.fill((255, 255, 0))
        self.image.set_alpha(100)
        screen.blit(self.image, [0, 0])
        pg.display.update()
        time.sleep(0.05)
        for emy in emys:
            emy.interval = float("inf")
            emy.image = pg.transform.laplacian(emy.image)
            emy.image.set_colorkey((0, 0, 0))
        for bomb in bombs:
            bomb.speed = bomb.speed / 2
            bomb.state = "inactive"


class TimeUP_emp:
    """
    empのクールタイムを表示するクラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"emp_cooldown: {int(self.value/50)}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 150, HEIGHT-100

    def update(self, screen: pg.Surface):
        if self.value > 0:
            self.value -= 1
        self.image = self.font.render(f"emp_cooldown: {int(self.value/50)}", 0, self.color)
        screen.blit(self.image, self.rect)


class TimeUP_Gravity:
    """
    Gravityのクールタイムを表示するクラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"gra_cooldown: {int(self.value/50)}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 150, HEIGHT-150

    def update(self, screen: pg.Surface):
        if self.value > 0:
            self.value -= 1
        self.image = self.font.render(f"gra_cooldown: {int(self.value/50)}", 0, self.color)
        screen.blit(self.image, self.rect)


class TimeUP_Hyper:
    """
    hyperのクールタイムを表示するクラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"hyper_cooldown: {int(self.value/50)}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 160, HEIGHT-200

    def update(self, screen: pg.Surface):
        if self.value > 0:
            self.value -= 1
        self.image = self.font.render(f"hyper_cooldown: {int(self.value/50)}", 0, self.color)
        screen.blit(self.image, self.rect)


class Mylife:
    """
    自機の残機を表示するクラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.txt = self.font.render(f"Life:", 0, (0, 0, 255))
        self.image = pg.image.load(f"fig/heart.png")

    def update(self, screen: pg.Surface, bird: Bird):
        screen.blit(self.txt, [40, 75])
        for i in range(bird.life):
            screen.blit(self.image, [120+(30*i), 85])


class Beamremain:
    """
    ビームの残弾数を管理するクラス。
    ビームの残弾数は self.remain に格納され、update メソッドでリロードされる（リロード時間は2秒）。
    hyouji メソッドで残弾数を画面の左下に表示する。
    """

    def __init__(self, screen:pg.Surface) -> None:
        self.count = 0  # リロードのカウントを管理する変数
        self.remain = 20  # 初期残弾数
        self.screen = screen  # 描画対象のスクリーン
        # ビームの画像を90度回転して読み込み、re_bm_imgに格納
        self.re_bm_img = pg.transform.rotate(pg.image.load("fig/beam.png"), 90)
        # 初期残弾数分のビーム画像をスクリーンに描画
        for i in range(self.remain):
            self.screen.blit(self.re_bm_img, [200+i*20, HEIGHT-70])
    
    def update(self):
        # 残弾数が0の場合、リロードのカウントを増やす
        if self.remain <= 0:
            self.count += 1
        else:
            # 残弾数がある場合はカウントをリセット
            self.count = 0
        # カウントが100に達したら、残弾数を20にリセット（リロード完了）
        if self.count >= 100:
            self.remain = 20
        for i in range(self.remain):
            self.screen.blit(self.re_bm_img, [250+i*20, HEIGHT-70])


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    bg_img2 = pg.transform.flip(bg_img, True, False)
    score = Score()
    wave = Wave(1)
    timeup_emp = TimeUP_emp()
    timeup_gravity = TimeUP_Gravity()
    timeup_hyper = TimeUP_Hyper()
    lifes = Mylife()

    bird = Bird(3, (900, 400), "normal", 0)
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    gra = pg.sprite.Group()
    num = 4  # 複数方向へ放つ時のビームの数
    remain=Beamremain(screen)
    tmr = 0
    clock = pg.time.Clock()

    while True:

        key_lst = pg.key.get_pressed()

        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_r:
                remain.remain=0
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird, 0))
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and timeup_hyper.value == 0: #クールタイムが0の時
                bird.state = "hyper"
                bird.hyper_life = 500
                timeup_hyper.value = 60*50 #クールタイムを設定
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and timeup_gravity.value == 0: #クールタイムが0の時
                gra.add(Gravity(400))
                timeup_gravity.value = 60*50 #クールタイムを設定
            if event.type == pg.KEYDOWN and event.key == pg.K_e and timeup_emp.value == 0: #クールタイムが0の時
                Emp(emys, bombs, screen)
                timeup_emp.value = 15*50 #クールタイムを設定
            if key_lst[pg.K_LSHIFT] and key_lst[pg.K_SPACE]:
                if remain.remain>0:
                    neobeam = Neobeam(bird, num)
                    beams.add(neobeam.gen_beams())  # BeamインスタンスのリストをBeamグループに追加
                    remain.remain-=num
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if remain.remain>0:
                    beams.add(Beam(bird, 0))
                    remain.remain-=1
        for bomb in pg.sprite.groupcollide(bombs, gra, True, False).keys():
            exps.add(Explosion(bomb, 50)) # 爆発エフェクト爆弾
        for emy in pg.sprite.groupcollide(emys, gra, True, False).keys():
            exps.add(Explosion(emy, 50)) # 爆発エフェクトエネミィ
            wave.killcount += 1 #Waveクラスのkillcount増加
        screen.blit(bg_img, [0, 0])

        for emy in emys:
            if emy.rect.center[0] <= 0:
                emy.kill()

        if wave.get_enemy_spawn(len(emys)):  # Waveクラスのget_enemy_spawn()関数から敵のスポーンができるかどうかを取得
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "normal" and tmr%emy.interval == 0:
                # 敵機が通常状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト
            wave.killcount += 1 #Waveクラスのkillcount増加

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        if len([bomb for bomb in pg.sprite.spritecollide(bird, bombs, True) if bomb.state != "inactive"]) != 0:
            if bird.state == "hyper":
                score.value += 1
                wave.killcount += 1 #Waveクラスのkillcount増加
                exps.add(Explosion(bird, 100))
            elif bird.life > 1:
                bird.life -= 1
            else:
                bird.life -= 1
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                lifes.update(screen, bird)
                pg.display.update()
                time.sleep(2)
                return
        if wave.killcount >= wave.finish_killcount:
            wave = Wave(wave.wave + 1)

        x = (tmr*10)%3200 # 背景の動くスピードを調整
        screen.blit(bg_img, [-x, 0]) # 背景を動かす
        screen.blit(bg_img2, [-x+1600, 0])
        screen.blit(bg_img, [-x+3200, 0])
        screen.blit(bg_img2, [-x+4800, 0])
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        gra.update(screen)
        score.update(screen)
        timeup_emp.update(screen)
        timeup_gravity.update(screen)
        timeup_hyper.update(screen)
        lifes.update(screen, bird)
        remain.update()
        wave.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
