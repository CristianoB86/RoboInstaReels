import os
import time
import random
import textwrap
import schedule
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI
from instagrapi import Client
from moviepy.editor import ImageClip, AudioFileClip

# ==========================
# CONFIGURAÇÕES
# ==========================
PASTA_IMAGENS = "imagens"
PASTA_MUSICAS = "musicas"
PASTA_FONTS = "fonts"
PASTA_ASSETS = "assets"
PASTA_FUNDOS = os.path.join(PASTA_ASSETS, "fundos")  # fundos aleatórios

for pasta in [PASTA_IMAGENS, PASTA_MUSICAS, PASTA_FONTS, PASTA_ASSETS, PASTA_FUNDOS]:
    if not os.path.exists(pasta):
        os.makedirs(pasta)

LARGURA_IMG = 1080
ALTURA_IMG = 1080
FONTE_CAMINHO = os.path.join(PASTA_FONTS, "seguiemj.ttf")
FONTE_TAMANHO = 50
ASPAS_TAMANHO = 100
RODAPE_TAMANHO = 30
MARGEM_TEXTO = 100

# ==========================
# CONFIGURAR CLIENTE OPENAI
# ==========================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("⚠️ Variável de ambiente OPENAI_API_KEY não definida.")

client = OpenAI(api_key=OPENAI_API_KEY)

# ==========================
# FUNÇÕES
# ==========================
def gerar_frase_motivacional():
    filosofos = [
        "Friedrich Nietzsche",
        "Plato",
        "Aristotle",
        "Socrates",
        "Jean-Paul Sartre",
        "Karl Marx"
    ]

    filosofo = random.choice(filosofos)
    print(filosofo)

    prompt = (
        f"Crie uma frase motivacional curta em português, "
        f"com tom profundo e filosófico no estilo de {filosofo}. "
        "Não use emojis, hashtags, nem cite autores. "
        "Nunca repita o início das frases. "
        "Varie a construção: verbos, metáforas, perguntas, contrastes, imagens poéticas. "
        "A frase deve ter no máximo 110 caracteres."
    )

    while True:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            n=1,
        )
        frase = completion.choices[0].message.content.strip()

        # Aceita apenas se o comprimento for <= 110
        if len(frase) <= 110:
            return frase

def gerar_imagem_minimalista(frase, nome_arquivo):
    img = Image.new("RGB", (LARGURA_IMG, ALTURA_IMG), color="black")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(FONTE_CAMINHO, FONTE_TAMANHO)
        aspas_font = ImageFont.truetype(FONTE_CAMINHO, ASPAS_TAMANHO)
        rodape_font = ImageFont.truetype(FONTE_CAMINHO, RODAPE_TAMANHO)
    except:
        font = aspas_font = rodape_font = ImageFont.load_default()

    # ==========================
    # Fundo aleatório
    # ==========================
    fundos = [os.path.join(PASTA_FUNDOS, f) for f in os.listdir(PASTA_FUNDOS) 
              if f.lower().endswith((".jpg", ".png"))]

    if fundos:
        fundo_path = random.choice(fundos)
        try:
            fundo_img = Image.open(fundo_path).convert("RGBA").resize((LARGURA_IMG, ALTURA_IMG))
            alpha = Image.new("L", fundo_img.size, 80)  # transparência
            fundo_img.putalpha(alpha)
            base = Image.new("RGBA", (LARGURA_IMG, ALTURA_IMG), "black")
            img = Image.alpha_composite(base, fundo_img)
        except Exception as e:
            print(f"⚠️ Erro ao abrir fundo: {e}")
            img = Image.new("RGBA", (LARGURA_IMG, ALTURA_IMG), "black")
    else:
        print("⚠️ Nenhum fundo encontrado. Usando preto puro.")
        img = Image.new("RGBA", (LARGURA_IMG, ALTURA_IMG), "black")

    draw = ImageDraw.Draw(img)

    # ==========================
    # Texto centralizado
    # ==========================
    wrapped_text = textwrap.fill(frase, width=20)
    linhas = wrapped_text.split("\n")
    line_spacing = 15
    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    total_text_height = len(linhas) * line_height + (len(linhas)-1)*line_spacing
    text_y = (ALTURA_IMG - total_text_height) // 2

    for linha in linhas:
        bbox = draw.textbbox((0,0), linha, font=font)
        line_w = bbox[2] - bbox[0]
        text_x = (LARGURA_IMG - line_w)//2
        draw.text((text_x+3, text_y+3), linha, font=font, fill="black")  # sombra
        draw.text((text_x, text_y), linha, font=font, fill="white")      # texto
        text_y += line_height + line_spacing

    # Aspas decorativas
    aspas = "“”"
    bbox_aspas = draw.textbbox((0,0), aspas, font=aspas_font)
    aspas_w = bbox_aspas[2] - bbox_aspas[0]
    draw.text(((LARGURA_IMG - aspas_w)/2, MARGEM_TEXTO), aspas, font=aspas_font, fill=(255,200,100))

    # ==========================
    # Rodapé com ícones
    # ==========================
    watermark_layer = Image.new("RGBA", img.size, (0,0,0,0))
    watermark_draw = ImageDraw.Draw(watermark_layer)

    try:
        youtube_icon = Image.open(os.path.join(PASTA_ASSETS, "youtube.png")).convert("RGBA").resize((32,32))
        insta_icon = Image.open(os.path.join(PASTA_ASSETS, "instagram.png")).convert("RGBA").resize((32,32))
    except:
        youtube_icon = insta_icon = None

    rodape_youtube = "youtube.com/@asabedoriaoculta"
    rodape_insta = "@sabedoriaoculta.oficial"

    bbox_yt = watermark_draw.textbbox((0,0), rodape_youtube, font=rodape_font)
    bbox_ig = watermark_draw.textbbox((0,0), rodape_insta, font=rodape_font)
    yt_w = bbox_yt[2] - bbox_yt[0]
    ig_w = bbox_ig[2] - bbox_ig[0]
    base_y = ALTURA_IMG - RODAPE_TAMANHO - 100

    if youtube_icon:
        yt_x = (LARGURA_IMG - (yt_w+42))//2
        watermark_layer.paste(youtube_icon, (yt_x, base_y-5), youtube_icon)
        watermark_draw.text((yt_x+42, base_y), rodape_youtube, font=rodape_font, fill=(255,255,255,200))

    if insta_icon:
        ig_x = (LARGURA_IMG - (ig_w+42))//2
        watermark_layer.paste(insta_icon, (ig_x, base_y+40), insta_icon)
        watermark_draw.text((ig_x+42, base_y+40), rodape_insta, font=rodape_font, fill=(255,255,255,200))

    img = Image.alpha_composite(img.convert("RGBA"), watermark_layer)

    caminho = os.path.join(PASTA_IMAGENS, nome_arquivo)
    img.convert("RGB").save(caminho)

    # Thumbnail 9:16
    thumb = Image.new("RGB", (1080,1920), "black")
    pos_x = (1080 - img.width)//2
    pos_y = (1920 - img.height)//2
    thumb.paste(img, (pos_x,pos_y))
    caminho_thumb = os.path.join(PASTA_IMAGENS, "motivacional_thumb.jpg")
    thumb.save(caminho_thumb)

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{agora}] ✅ Imagem salva: {caminho}")
    print(f"[{agora}] ✅ Thumbnail salva: {caminho_thumb}")
    return caminho, caminho_thumb

def criar_video(imagem_path, video_path, duracao=10):
    clip = ImageClip(imagem_path).set_duration(duracao).set_fps(30)
    musicas = [os.path.join(PASTA_MUSICAS,f) for f in os.listdir(PASTA_MUSICAS) if f.lower().endswith((".mp3",".wav"))]
    if musicas:
        musica_escolhida = random.choice(musicas)
        print(f"🎶 Música escolhida: {os.path.basename(musica_escolhida)}")
        audio = AudioFileClip(musica_escolhida).subclip(0,duracao)
        clip = clip.set_audio(audio)
    else:
        print("⚠️ Nenhuma música encontrada. O vídeo será sem áudio.")
    clip.write_videofile(video_path, codec="libx264", audio_codec="aac")
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{agora}] 🎥 Vídeo salvo em: {video_path}")

def postar_reels(video, legenda, thumbnail_path):
    cl = Client()
    INSTAGRAM_USER = os.environ.get("IG_USER")
    INSTAGRAM_PASS = os.environ.get("IG_PASS")
    #INSTAGRAM_ID = os.environ.get("IG_SESSIONID")
    if not INSTAGRAM_USER or not INSTAGRAM_PASS:
        print("⚠️ Variáveis IG_USER ou IG_PASS não definidas. Não será postado.")
        return
    try:
#        cl.login_by_sessionid(INSTAGRAM_ID)
        cl.login(INSTAGRAM_USER, INSTAGRAM_PASS)
        cl.clip_upload(path=video, caption=legenda, thumbnail=thumbnail_path)
        print("✅ Reels postado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao postar no Instagram: {e}")

# ==========================
# TAREFA PRINCIPAL
# ==========================
def tarefa_postagem():
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{agora}] ⏰ Executando tarefa...")
    frase = gerar_frase_motivacional()
    print(f"[{agora}] Frase gerada: \"{frase}\"")
    img_path, thumb_path = gerar_imagem_minimalista(frase, "motivacional.jpg")
    video_path = os.path.join(PASTA_IMAGENS, "motivacional.mp4")
    criar_video(img_path, video_path, duracao=10)
    legenda = "Mensagem do dia ✨🔥 #motivação #sabedoria #reels"
    postar_reels(video_path, legenda, thumb_path)
    print("🚀 Postagem realizada:", datetime.now().strftime("%d/%m/%Y %H:%M"))

# ==========================
# AGENDAMENTO
# ==========================
#schedule.every().day.at("08:00").do(tarefa_postagem)
#schedule.every().day.at("12:00").do(tarefa_postagem)
#schedule.every().day.at("20:00").do(tarefa_postagem)

# Função para gerar horários aleatórios dentro dos intervalos
def gerar_horarios():
    horarios = [
        (9, 10),   # entre 9h e 10h
        (13, 14),  # entre 13h e 14h
        (17, 18),  # entre 17h e 18h
        (21, 22),  # entre 21h e 22h
        (1, 2)     # entre 1h e 2h
    ]

    agendados = []
    for inicio, fim in horarios:
        hora = random.randint(inicio, fim - 1)  # escolhe hora dentro do intervalo
        minuto = random.randint(0, 59)          # escolhe minuto aleatório
        agendados.append((hora, minuto))
    return agendados

if __name__ == "__main__":
    horarios_do_dia = gerar_horarios()
    print("📅 Agendamento configurado para hoje:", horarios_do_dia)

    while True:
        agora = datetime.now()
        hora_atual, minuto_atual = agora.hour, agora.minute

        if (hora_atual, minuto_atual) in horarios_do_dia:
            tarefa_postagem()
            # Depois que postar, remove o horário para não repetir no mesmo dia
            horarios_do_dia.remove((hora_atual, minuto_atual))

            # Se acabou todos os horários, gera novos para o próximo dia
            if not horarios_do_dia:
                print("✅ Todos os posts do dia feitos. Gerando novos horários para amanhã...")
                time.sleep(60)  # espera 1 minuto antes de gerar novos
                horarios_do_dia = gerar_horarios()
                print("📅 Novos horários gerados:", horarios_do_dia)

        time.sleep(20)  # checa a cada 20 segundos
