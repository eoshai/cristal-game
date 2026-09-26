from ursina import *
from ursina import application
from ursina.prefabs.first_person_controller import FirstPersonController
import math
import os
import random
import sys

app = Ursina()

# =========================================================
# 1. CONFIGURACOES GERAIS
# =========================================================
window.title = "O Resgate do Cristal 3D"
window.borderless = False
window.fps_counter.enabled = False
window.exit_button.visible = False

TEMPO_MAXIMO = 60                 # segundos no inicio da partida
INCREMENTO_DIFICULDADE = 0.15     # quanto o tempo acelera a cada chave coletada

DIST_COLETA_CHAVE = 2.2
DIST_INTERACAO_PORTAO = 2.5
DIST_INTERACAO_CRISTAL = 2.0

INTERVALO_PASSO = 0.35            # segundos entre sons de passo

# posicao original do portao, usada tanto pra criar quanto pra resetar
POSICAO_PORTAO = Vec3(0, 2.5, 20)
COR_PORTAO_TRANCADO = color.rgb(120, 35, 35)
COR_PORTAO_DESTRANCADO = color.rgb(90, 200, 90)

# =========================================================
# 2. CENARIO ESTATICO
# =========================================================
sky = Sky()
ground = Entity(model='plane', scale=(60, 1, 60), color=color.lime, texture='grass', collider='box')
scene.fog_color = color.light_gray
scene.fog_density = 0.015
DirectionalLight(y=2, z=3, shadows=True)

player = FirstPersonController(y=2, origin_y=-0.5, speed=8, jump_height=2.5)
player.cursor.color = color.red
player.enabled = False  # so e ativado quando o jogo comeca

# --- Muros externos ---
parede1 = Entity(model='cube', scale=(60, 5, 1), position=(0, 2.5, 30), color=color.gray, texture='brick', collider='box')
parede2 = Entity(model='cube', scale=(60, 5, 1), position=(0, 2.5, -30), color=color.gray, texture='brick', collider='box')
parede3 = Entity(model='cube', scale=(1, 5, 60), position=(30, 2.5, 0), color=color.gray, texture='brick', collider='box')
parede4 = Entity(model='cube', scale=(1, 5, 60), position=(-30, 2.5, 0), color=color.gray, texture='brick', collider='box')

# --- Labirinto interno ---
labirinto = [
    Entity(model='cube', scale=(20, 4, 1), position=(-10, 2, -18), color=color.dark_gray, texture='brick', collider='box'),
    Entity(model='cube', scale=(20, 4, 1), position=(10, 2, -5), color=color.dark_gray, texture='brick', collider='box'),
    Entity(model='cube', scale=(1, 4, 20), position=(-5, 2, 5), color=color.dark_gray, texture='brick', collider='box'),
    Entity(model='cube', scale=(1, 4, 18), position=(18, 2, 4), color=color.dark_gray, texture='brick', collider='box'),
    Entity(model='cube', scale=(15, 4, 1), position=(-18, 2, 0), color=color.dark_gray, texture='brick', collider='box'),
    Entity(model='cube', scale=(1, 4, 14), position=(-22, 2, 8), color=color.dark_gray, texture='brick', collider='box'),
]

# --- Plataformas (obrigam o jogador a pular) ---
plataformas = [
    Entity(model='cube', scale=(4, 0.5, 4), position=(15, 1, 15), color=color.brown, texture='brick', collider='box'),
    Entity(model='cube', scale=(4, 0.5, 4), position=(15, 2.2, 20), color=color.brown, texture='brick', collider='box'),
    Entity(model='cube', scale=(4, 0.5, 4), position=(11, 3.4, 24), color=color.brown, texture='brick', collider='box'),
]

# --- Jaula do cristal ---
# O cristal fica cercado por paredes solidas (a colisao de verdade) com
# barras decorativas por cima pra parecer uma jaula. A UNICA entrada e
# o portao (POSICAO_PORTAO); sem essas paredes laterais, dava pra
# simplesmente andar por fora do portao e pegar o cristal sem as chaves.
def criar_parede_jaula(x):
    # zona vai de z=19.5 (encostando no portao) ate z=30.5 (sobrepondo
    # o muro externo de propósito, pra nao sobrar nenhuma fresta na junta)
    Entity(model='cube', color=color.rgba(35, 35, 40, 90), scale=(1, 5, 11),
           position=(x, 2.5, 25.25), collider='box')
    for z in range(20, 31):
        Entity(model='cube', color=color.light_gray, scale=(0.08, 5, 0.08),
               position=(x, 2.5, z), collider=None)

criar_parede_jaula(-4)
criar_parede_jaula(4)

# parede de fundo extra, soh por segurança, sobrepondo o muro externo
fundo_jaula = Entity(model='cube', color=color.rgba(35, 35, 40, 90), scale=(8, 5, 1.2),
                      position=(0, 2.5, 29.6), collider='box')

portao = Entity(model='cube', color=COR_PORTAO_TRANCADO, scale=(8, 5, 1), position=POSICAO_PORTAO, collider='box')

# cadeado decorativo (corpo + alça), soh pra deixar claro que o portao esta trancado
cadeado_corpo = Entity(parent=portao, model='cube', color=color.yellow, scale=(0.045, 0.16, 0.14), position=(0, -0.06, 0))
cadeado_alca_esq = Entity(parent=portao, model='cube', color=color.light_gray, scale=(0.045, 0.14, 0.03), position=(0, 0.04, -0.05))
cadeado_alca_dir = Entity(parent=portao, model='cube', color=color.light_gray, scale=(0.045, 0.14, 0.03), position=(0, 0.04, 0.05))
cadeado_alca_topo = Entity(parent=portao, model='cube', color=color.light_gray, scale=(0.045, 0.03, 0.14), position=(0, 0.10, 0))
portao_aberto = False

# =========================================================
# 3. SONS E MUSICA (Corrigido para Executável e FPS)
# =========================================================
# Força o Python a usar o diretório onde o arquivo .exe está localizado
if getattr(sys, 'frozen', False):
    pasta_exe = os.path.dirname(sys.executable)
    os.chdir(pasta_exe)

def carregar_som(nome_base, **kwargs):
    """ Busca os arquivos .wav/ogg/mp3 na pasta sounds/ ao lado do EXE """
    for ext in ('.wav', '.ogg', '.mp3'):
        caminho = os.path.join('sounds', f'{nome_base}{ext}')
        if os.path.exists(caminho):
            try:
                # Passa o caminho normalizado para a Ursina
                som = Audio(caminho.replace('\\', '/'), autoplay=False, **kwargs)
                print(f"[audio] Som '{caminho}' carregado com sucesso!")
                return som
            except Exception as e:
                print(f"[audio] Erro ao carregar '{caminho}': {e}")
    print(f"[audio] Nao encontrou '{nome_base}' na pasta sounds/")
    return None

# Sons customizados
musica_fundo = carregar_som('musica_fundo', loop=True, volume=1.0)
som_chave = carregar_som('coletar_chave', volume=0.6)
som_portao = carregar_som('abrir_portao', volume=0.6)
som_vitoria = carregar_som('vitoria', volume=0.7)
som_derrota = carregar_som('derrota', volume=0.7)
som_passo = carregar_som('passo', volume=0.25)

# Sons reserva pré-carregados (EVITA QUEDAS DE FPS)
reserva_beep = Audio('beep', autoplay=False, pitch=1.2, volume=0.5)
reserva_coin = Audio('coin', autoplay=False, pitch=1.4, volume=0.6)
reserva_passo = Audio('beep', autoplay=False, pitch=1.8, volume=0.15)

def tocar(som_customizado, som_reserva_obj, pitch=1.0, volume=0.5):
    """Toca o som sem instanciar novos objetos na memória."""
    if som_customizado:
        som_customizado.pitch = pitch
        som_customizado.volume = volume
        som_customizado.play()
    elif som_reserva_obj:
        som_reserva_obj.pitch = pitch
        som_reserva_obj.volume = volume
        som_reserva_obj.play()

def tocar_musica():
    if musica_fundo:
        try:
            musica_fundo.play()
        except Exception as e:
            print(f"[audio] ERRO ao tocar musica_fundo: {e}")

def parar_musica():
    if musica_fundo:
        try:
            if getattr(musica_fundo, 'playing', True):
                musica_fundo.stop()
        except Exception as e:
            print(f"[audio] ERRO ao parar musica_fundo: {e}")

# =========================================================
# 4. CHAVE ESTILIZADA (anel + haste + dentes, feita so com cubos)
# A chave sempre "olha" para o jogador (billboard).
# =========================================================
def criar_chave(posicao):
    grupo = Entity(position=posicao)

    raio = 0.32
    segmentos = 10
    for i in range(segmentos):
        ang = (360 / segmentos) * i
        rad = math.radians(ang)
        x = math.cos(rad) * raio
        y = math.sin(rad) * raio
        Entity(parent=grupo, model='cube', color=color.gold,
               scale=(0.16, 0.09, 0.08), position=(x, y, 0),
               rotation=(0, 0, ang))

    Entity(parent=grupo, model='cube', color=color.gold,
           scale=(0.13, 0.55, 0.1), position=(0, -0.55, 0))
    Entity(parent=grupo, model='cube', color=color.gold,
           scale=(0.24, 0.09, 0.1), position=(0.12, -0.82, 0))
    Entity(parent=grupo, model='cube', color=color.gold,
           scale=(0.24, 0.09, 0.1), position=(0.12, -1.0, 0))

    grupo.collider = None
    return grupo


# =========================================================
# 5. ELEMENTOS DA MISSAO
# =========================================================
posicoes_chaves = [
    Vec3(-15, 1.8, -10),
    Vec3(15, 1.8, 10),
    Vec3(11, 4.5, 24),
]
chaves = [criar_chave(pos) for pos in posicoes_chaves]

auras = [
    Entity(model='sphere', color=color.yellow, scale=1.0, alpha=0.18, position=pos, collider=None)
    for pos in posicoes_chaves
]

cristal = Entity(model='diamond', color=color.cyan, scale=1.5, position=(0, 2, 25), collider='box')

# =========================================================
# VARIAVEIS DE ESTADO DO JOGO
# =========================================================
chaves_recolhidas = 0
tempo_restante = TEMPO_MAXIMO
multiplicador_tempo = 1.0
estado_jogo = "menu"          # "menu" | "jogando" | "vitoria" | "derrota"
confirmando_saida = False
jogador_ativo_antes_de_sair = False
tempo_desde_passo = 0.0

# =========================================================
# 6. INTERFACE (paineis, HUD, menu, telas de fim, confirmacao de saida)
# =========================================================
def criar_painel(largura, altura, posicao=(0, 0)):
    # z maior = mais pro fundo, z menor = mais pra frente (evita as duas
    # camadas de UI brigarem pelo mesmo plano, o chamado "z-fighting")
    borda = Entity(parent=camera.ui, model='quad', color=color.gold,
                    scale=(largura + 0.035, altura + 0.035), position=posicao, z=0.02)
    fundo = Entity(parent=camera.ui, model='quad', color=color.black90,
                    scale=(largura, altura), position=posicao, z=0.01)
    return borda, fundo

# --- Painel do menu ---
borda_menu, fundo_menu = criar_painel(0.85, 0.58, (0, 0.02))
titulo_menu = Text(text="O RESGATE DO CRISTAL", origin=(0, 0), position=(0, 0.27), scale=2.2, color=color.gold, z=-0.01)
linha_menu = Entity(parent=camera.ui, model='quad', color=color.gold, scale=(0.65, 0.005), position=(0, 0.20), z=-0.01)
subtitulo_menu = Text(
    text="Colete as 3 chaves, abra o portao da jaula\ne recupere o cristal antes que o tempo acabe!",
    origin=(0, 0), position=(0, 0.08), scale=0.9, color=color.white, z=-0.01
)
instrucao_menu = Text(
    text="WASD mover | Espaco pular | Mouse olhar | ESC sair",
    origin=(0, 0), position=(0, -0.08), scale=0.75, color=color.light_gray, z=-0.01
)
chamada_menu = Text(text="PRESSIONE ENTER PARA COMECAR", origin=(0, 0), position=(0, -0.19), scale=1.1, color=color.yellow, z=-0.01)
elementos_menu = [borda_menu, fundo_menu, titulo_menu, linha_menu, subtitulo_menu, instrucao_menu, chamada_menu]

# --- Painel de fim de jogo (vitoria / derrota) ---
borda_msg, fundo_msg = criar_painel(0.75, 0.32, (0, 0.02))
mensagem_central = Text(text="", origin=(0, 0), position=(0, 0.1), scale=1.6, color=color.white, z=-0.01)
detalhe_central = Text(text="", origin=(0, 0), position=(0, -0.02), scale=0.85, color=color.light_gray, z=-0.01)
reinicio_central = Text(text="", origin=(0, 0), position=(0, -0.11), scale=0.9, color=color.yellow, z=-0.01)
elementos_fim = [borda_msg, fundo_msg, mensagem_central, detalhe_central, reinicio_central]
for e in elementos_fim:
    e.enabled = False

# --- Painel de confirmacao de saida (ESC) ---
borda_sair, fundo_sair = criar_painel(0.62, 0.28, (0, 0))
texto_sair = Text(text="Sair do jogo?", origin=(0, 0), position=(0, 0.06), scale=1.3, color=color.white, z=-0.01)
texto_sair_opcoes = Text(text="ENTER = Sim        ESC = Cancelar", origin=(0, 0), position=(0, -0.06), scale=0.85, color=color.yellow, z=-0.01)
elementos_sair = [borda_sair, fundo_sair, texto_sair, texto_sair_opcoes]
for e in elementos_sair:
    e.enabled = False

# --- HUD (durante o jogo) ---
hud_texto = Text(text="Chaves: 0/3  |  Tempo: 60s", position=(-0.85, 0.45), scale=1.6, color=color.yellow)
hud_texto.enabled = False

_pontos_seta = [Vec3(-0.02, -0.018, 0), Vec3(0.02, -0.018, 0), Vec3(0, 0.03, 0)]
seta_indicador = Entity(parent=camera.ui, model=Mesh(vertices=_pontos_seta, mode='triangle'),
                         color=color.azure, position=(0, 0.35))
seta_indicador.enabled = False


# =========================================================
# 7. EFEITOS VISUAIS
# =========================================================
def criar_pulso_luz(posicao):
    pulso = Entity(model='sphere', color=color.yellow, position=posicao, scale=0.5, alpha=0.8, collider=None)
    pulso.animate_scale(4, duration=0.4, curve=curve.out_expo)
    pulso.fade_out(duration=0.4)
    destroy(pulso, delay=0.5)

    luz = PointLight(position=posicao, color=color.yellow, y=posicao.y + 1)
    destroy(luz, delay=0.5)


def criar_confete(posicao, quantidade=22):
    cores = [color.gold, color.yellow, color.orange, color.white, color.cyan]
    for _ in range(quantidade):
        p = Entity(model='cube', color=random.choice(cores), scale=0.18, position=posicao, collider=None)
        alvo = posicao + Vec3(random.uniform(-4, 4), random.uniform(1, 5), random.uniform(-4, 4))
        p.animate_position(alvo, duration=random.uniform(0.7, 1.2), curve=curve.out_expo)
        p.animate_rotation((random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360)), duration=1.2)
        p.fade_out(duration=1.0, delay=0.5)
        destroy(p, delay=1.8)


def animar_entrada(entidade, escala_final, atraso=0.0):
    entidade.scale = 0
    entidade.animate_scale(escala_final, duration=0.6, delay=atraso, curve=curve.out_bounce)


def abrir_portao():
    """Toca a animacao/som do portao e libera a passagem pra jaula."""
    global portao_aberto
    portao_aberto = True
    portao.color = COR_PORTAO_DESTRANCADO
    portao.collider = None  # libera a passagem imediatamente
    portao.animate_position(POSICAO_PORTAO + Vec3(0, -4.3, 0), duration=0.8, curve=curve.in_quad)
    tocar(som_portao, reserva_coin, pitch=0.8, volume=0.5)


def resetar_portao():
    global portao_aberto
    portao_aberto = False
    portao.color = COR_PORTAO_TRANCADO
    portao.collider = 'box'
    portao.position = POSICAO_PORTAO


# =========================================================
# 8. CONTROLE DE ESTADOS DO JOGO
# =========================================================
def iniciar_jogo():
    global chaves_recolhidas, tempo_restante, multiplicador_tempo, estado_jogo, tempo_desde_passo

    chaves_recolhidas = 0
    tempo_restante = TEMPO_MAXIMO
    multiplicador_tempo = 1.0
    tempo_desde_passo = 0.0
    estado_jogo = "jogando"

    for chave, aura in zip(chaves, auras):
        chave.enabled = True
        aura.enabled = True
    cristal.enabled = True
    resetar_portao()

    for e in elementos_menu:
        e.enabled = False
    for e in elementos_fim:
        e.enabled = False
    mensagem_central.text = ""
    detalhe_central.text = ""
    reinicio_central.text = ""

    hud_texto.enabled = True
    seta_indicador.enabled = True

    player.enabled = True
    player.position = (0, 2, -25)
    player.rotation = (0, 0, 0)
    player.camera_pivot.rotation_x = 0
    mouse.locked = True

    tocar_musica()


def mostrar_menu():
    global estado_jogo
    estado_jogo = "menu"

    for e in elementos_menu:
        e.enabled = True
    animar_entrada(titulo_menu, 3)
    animar_entrada(subtitulo_menu, 1.3, atraso=0.12)
    animar_entrada(instrucao_menu, 1.1, atraso=0.22)
    animar_entrada(chamada_menu, 1.6, atraso=0.32)

    for e in elementos_fim:
        e.enabled = False
    mensagem_central.text = ""
    detalhe_central.text = ""
    reinicio_central.text = ""

    hud_texto.enabled = False
    seta_indicador.enabled = False
    player.enabled = False
    mouse.locked = False

    parar_musica()


def abrir_confirmacao_saida():
    global confirmando_saida, jogador_ativo_antes_de_sair
    confirmando_saida = True
    jogador_ativo_antes_de_sair = player.enabled
    player.enabled = False
    mouse.locked = False
    for e in elementos_sair:
        e.enabled = True
    animar_entrada(texto_sair, 1.3)


def fechar_confirmacao_saida():
    global confirmando_saida
    confirmando_saida = False
    for e in elementos_sair:
        e.enabled = False
    if jogador_ativo_antes_de_sair:
        player.enabled = True
        mouse.locked = True


# =========================================================
# 9. INPUT E LOOP PRINCIPAL
# =========================================================
def input(key):
    if key == 'escape':
        if confirmando_saida:
            fechar_confirmacao_saida()
        else:
            abrir_confirmacao_saida()
        return

    if confirmando_saida:
        if key == 'enter':
            application.quit()
        return

    if estado_jogo == "menu" and key == "enter":
        iniciar_jogo()
    elif estado_jogo in ("vitoria", "derrota") and key == "r":
        mostrar_menu()


def update():
    global chaves_recolhidas, tempo_restante, multiplicador_tempo, estado_jogo, tempo_desde_passo

    if confirmando_saida:
        return
    if estado_jogo != "jogando":
        return

    # --- animacao das chaves (flutuando + sempre viradas pro jogador) e do cristal ---
    for chave, aura, pos_base in zip(chaves, auras, posicoes_chaves):
        if chave.enabled:
            chave.y = pos_base.y + math.sin(time.time() * 2 + pos_base.x) * 0.15
            direcao = player.world_position - chave.world_position
            chave.rotation_y = math.degrees(math.atan2(direcao.x, direcao.z))
            aura.rotation_y -= 80 * time.dt
            aura.position = chave.position
            aura.scale = 1.0 + math.sin(time.time() * 4) * 0.08
    cristal.rotation_y += 100 * time.dt

    # --- som de passos ---
    andando = held_keys['w'] or held_keys['a'] or held_keys['s'] or held_keys['d']
    no_chao = getattr(player, 'grounded', True)
    if andando and no_chao:
        tempo_desde_passo += time.dt
        if tempo_desde_passo >= INTERVALO_PASSO:
            tempo_desde_passo = 0
            tocar(som_passo, reserva_passo, pitch=1.8, volume=0.15)
    else:
        tempo_desde_passo = INTERVALO_PASSO

    # --- contagem do tempo (com dificuldade progressiva) ---
    tempo_restante -= time.dt * multiplicador_tempo
    segundos = max(0, int(tempo_restante))

    if tempo_restante <= 10:
        pulso = 1.6 + math.sin(time.time() * 10) * 0.25
        hud_texto.scale = pulso
        hud_texto.color = color.red
    else:
        hud_texto.scale = 1.6
        hud_texto.color = color.yellow

    hud_texto.text = f"Chaves: {chaves_recolhidas}/3  |  Tempo: {segundos}s"

    # --- seta indicadora: aponta pra chave mais proxima, depois pro portao/cristal ---
    alvo = None
    for chave in chaves:
        if chave.enabled:
            alvo = chave
            break
    if alvo is None:
        alvo = cristal if cristal.enabled else portao

    direcao = alvo.world_position - player.world_position
    angulo_alvo = math.degrees(math.atan2(direcao.x, direcao.z))
    angulo_relativo = (angulo_alvo - player.rotation_y + 180) % 360 - 180
    seta_indicador.rotation_z = -angulo_relativo

    # --- derrota ---
    if tempo_restante <= 0:
        estado_jogo = "derrota"
        for e in elementos_fim:
            e.enabled = True
        mensagem_central.text = "GAME OVER!"
        mensagem_central.color = color.red
        detalhe_central.text = "O tempo acabou antes de voce recuperar o cristal."
        reinicio_central.text = "Pressione R para voltar ao menu"
        animar_entrada(mensagem_central, 2.2)
        hud_texto.enabled = False
        seta_indicador.enabled = False
        player.enabled = False
        mouse.locked = False
        parar_musica()
        tocar(som_portao, reserva_coin, pitch=0.8, volume=0.5)
        return

    # --- coleta de chaves ---
    for chave, aura in zip(chaves, auras):
        if chave.enabled and distance(player.position, chave.position) < DIST_COLETA_CHAVE:
            chave.enabled = False
            aura.enabled = False
            chaves_recolhidas += 1
            multiplicador_tempo += INCREMENTO_DIFICULDADE
            criar_pulso_luz(chave.position)
            tocar(som_chave, reserva_beep, pitch=1.2, volume=0.5)

    # --- portao da jaula ---
    if not portao_aberto and distance(player.position, portao.position) < DIST_INTERACAO_PORTAO:
        if chaves_recolhidas >= 3:
            abrir_portao()
        else:
            empurrao = (player.position - portao.position)
            empurrao.y = 0
            player.position += empurrao.normalized() * 0.3

    # --- vitoria ---
    if cristal.enabled and distance(player.position, cristal.position) < DIST_INTERACAO_CRISTAL:
        estado_jogo = "vitoria"
        cristal.enabled = False

        segundos_restantes = max(0, int(tempo_restante))
        if segundos_restantes >= 30:
            rank = "S"
        elif segundos_restantes >= 15:
            rank = "A"
        else:
            rank = "B"

        for e in elementos_fim:
            e.enabled = True
        mensagem_central.text = "CRISTAL RECUPERADO!"
        mensagem_central.color = color.green
        detalhe_central.text = f"Tempo restante: {segundos_restantes}s   |   Rank: {rank}"
        reinicio_central.text = "Pressione R para voltar ao menu"
        animar_entrada(mensagem_central, 2.2)

        criar_confete(cristal.position)
        hud_texto.enabled = False
        seta_indicador.enabled = False
        parar_musica()
        tocar(som_vitoria, reserva_coin, pitch=1.4, volume=0.6)
        player.enabled = False
        mouse.locked = False


mostrar_menu()
app.run()
