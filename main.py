"""Bot do Telegram que consulta o clima na WeatherAPI e responde com um card em imagem."""

import os

import requests
import telebot
from PIL import Image, ImageDraw, ImageFont

# As chaves ficam em variáveis de ambiente, nunca no código
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

if not TELEGRAM_TOKEN or not WEATHER_API_KEY:
    raise SystemExit("Defina as variáveis de ambiente TELEGRAM_TOKEN e WEATHER_API_KEY.")

PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
PASTA_IMAGENS = os.path.join(PASTA_BASE, "imagens")
CAMINHO_CARD = os.path.join(PASTA_IMAGENS, "clima.png")
CAMINHO_FUNDO = os.path.join(PASTA_BASE, "fundo.png")
FONTE_TITULO = os.path.join(PASTA_BASE, "fontes", "LiberationSerif-Bold.ttf")
FONTE_TEXTO = os.path.join(PASTA_BASE, "fontes", "LiberationSerif-Regular.ttf")
URL_API = "http://api.weatherapi.com/v1/current.json"
COR_TEXTO = "#404040"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 5.1 Cria a pasta de imagens, caso ainda não exista
if not os.path.exists(PASTA_IMAGENS):
    os.makedirs(PASTA_IMAGENS)


def buscar_clima(cidade):
    """Consulta a WeatherAPI e devolve um dicionário com os dados do card, ou None se falhar."""
    parametros = {"key": WEATHER_API_KEY, "q": cidade, "lang": "pt"}
    try:
        resposta = requests.get(URL_API, params=parametros, timeout=10)
    except requests.RequestException:
        return None

    if resposta.status_code != 200:
        return None

    dados = resposta.json()
    return {
        "cidade": dados["location"]["name"],
        "pais": dados["location"]["country"],
        "temperatura": dados["current"]["temp_c"],
        "sensacao": dados["current"]["feelslike_c"],
        "umidade": dados["current"]["humidity"],
        "clima": dados["current"]["condition"]["text"],
    }


def gerar_card(info, caminho):
    """Desenha o card com Pillow sobre a imagem de fundo e salva em `caminho`."""
    # 5.3 Remove a imagem anterior antes de gerar a nova
    if os.path.exists(caminho):
        os.remove(caminho)

    imagem = Image.open(CAMINHO_FUNDO).convert("RGBA")

    # Painel translúcido para o texto ficar legível sobre as nuvens
    painel = Image.new("RGBA", imagem.size, (0, 0, 0, 0))
    ImageDraw.Draw(painel).rounded_rectangle((50, 55, 560, 470), radius=24, fill=(255, 255, 255, 150))
    imagem = Image.alpha_composite(imagem, painel)

    desenhar = ImageDraw.Draw(imagem)
    fonte_titulo = ImageFont.truetype(FONTE_TITULO, 40)
    fonte_texto = ImageFont.truetype(FONTE_TEXTO, 30)

    desenhar.text((80, 80), "PREVISÃO DO TEMPO", fill=COR_TEXTO, font=fonte_titulo)

    linhas = [
        f"Cidade: {info['cidade']}",
        f"País: {info['pais']}",
        f"Temperatura: {info['temperatura']} °C",
        f"Sensação: {info['sensacao']} °C",
        f"Umidade: {info['umidade']}%",
        f"Clima: {info['clima']}",
    ]
    for i, linha in enumerate(linhas):
        desenhar.text((80, 170 + i * 50), linha, fill=COR_TEXTO, font=fonte_texto)

    # 5.2 Salva a imagem dentro da pasta imagens/
    imagem.convert("RGB").save(caminho)


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Olá! Digite o nome de uma cidade para consultar o clima.\n"
        "Exemplo: Blumenau\n\n"
        "Se existir mais de uma cidade com o mesmo nome, inclua o país. Exemplo: Toledo, Brazil",
    )


@bot.message_handler(func=lambda message: True)
def clima(message):
    info = buscar_clima(message.text)
    if info is None:
        bot.send_message(message.chat.id, "Não encontrei essa cidade. Confira o nome e tente de novo.")
        return

    gerar_card(info, CAMINHO_CARD)
    with open(CAMINHO_CARD, "rb") as foto:
        bot.send_photo(message.chat.id, foto)


if __name__ == "__main__":
    print("Bot em execução. Pressione Ctrl+C para encerrar.")
    bot.infinity_polling()
