"""Bot do Telegram que consulta o clima na WeatherAPI e responde com um card em imagem."""

import logging
import os

import requests
import telebot
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bot-clima")

# As chaves ficam em variáveis de ambiente, nunca no código
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

PASTA_BASE = os.path.dirname(os.path.abspath(__file__))
PASTA_IMAGENS = os.path.join(PASTA_BASE, "imagens")
CAMINHO_FUNDO = os.path.join(PASTA_BASE, "fundo.png")
FONTE_TITULO = os.path.join(PASTA_BASE, "fontes", "LiberationSerif-Bold.ttf")
FONTE_TEXTO = os.path.join(PASTA_BASE, "fontes", "LiberationSerif-Regular.ttf")

URL_BUSCA = "https://api.weatherapi.com/v1/search.json"
URL_CLIMA = "https://api.weatherapi.com/v1/current.json"
TEMPO_LIMITE = 10  # segundos para cada requisição

COR_TEXTO = "#404040"
LARGURA_MAXIMA_TEXTO = 460  # largura útil do painel, em pixels

# A WeatherAPI devolve o nome do país em inglês, mesmo com lang=pt
PAISES_PT = {
    "Brazil": "Brasil",
    "United States of America": "Estados Unidos",
    "Argentina": "Argentina",
    "Portugal": "Portugal",
    "Spain": "Espanha",
    "France": "França",
    "Germany": "Alemanha",
    "Italy": "Itália",
    "United Kingdom": "Reino Unido",
    "Japan": "Japão",
    "Mexico": "México",
    "Chile": "Chile",
    "Uruguay": "Uruguai",
    "Paraguay": "Paraguai",
}

# validate_token=False permite importar o módulo nos testes sem um token real
bot = telebot.TeleBot(TELEGRAM_TOKEN or "", validate_token=False)


def formatar_numero(valor):
    """Formata 18.0 como '18' e 15.1 como '15,1', no padrão brasileiro."""
    if float(valor).is_integer():
        return str(int(valor))
    return f"{valor:.1f}".replace(".", ",")


def escolher_local(cidade):
    """Procura a cidade e dá preferência a resultados no Brasil.

    Sem isso, "Toledo" vira Toledo, nos Estados Unidos, em vez de Toledo, no Paraná.
    Devolve a consulta a usar na WeatherAPI ("lat,lon") ou o próprio texto digitado.
    """
    if "," in cidade:  # o usuário já informou o país ou o estado
        return cidade
    try:
        resposta = requests.get(
            URL_BUSCA, params={"key": WEATHER_API_KEY, "q": cidade}, timeout=TEMPO_LIMITE
        )
        resposta.raise_for_status()
        resultados = resposta.json()
    except (requests.RequestException, ValueError):
        log.warning("Busca de cidade falhou para %r", cidade)
        return cidade

    for local in resultados:
        if local.get("country") == "Brazil":
            return f"{local['lat']},{local['lon']}"
    return cidade


def buscar_clima(cidade):
    """Consulta a WeatherAPI e devolve um dicionário com os dados do card, ou None se falhar."""
    parametros = {"key": WEATHER_API_KEY, "q": escolher_local(cidade), "lang": "pt"}
    try:
        resposta = requests.get(URL_CLIMA, params=parametros, timeout=TEMPO_LIMITE)
    except requests.RequestException:
        log.exception("Erro de conexão com a WeatherAPI")
        return None

    if resposta.status_code != 200:
        log.info("Cidade não encontrada: %r (HTTP %s)", cidade, resposta.status_code)
        return None

    dados = resposta.json()
    pais = dados["location"]["country"]
    return {
        "cidade": dados["location"]["name"],
        "pais": PAISES_PT.get(pais, pais),
        "temperatura": dados["current"]["temp_c"],
        "sensacao": dados["current"]["feelslike_c"],
        "umidade": dados["current"]["humidity"],
        "clima": dados["current"]["condition"]["text"],
    }


def fonte_que_cabe(desenhar, texto, caminho_fonte, tamanho):
    """Diminui a fonte até o texto caber na largura do painel."""
    while tamanho > 16:
        fonte = ImageFont.truetype(caminho_fonte, tamanho)
        if desenhar.textlength(texto, font=fonte) <= LARGURA_MAXIMA_TEXTO:
            return fonte
        tamanho -= 2
    return ImageFont.truetype(caminho_fonte, tamanho)


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
    desenhar.text((80, 80), "PREVISÃO DO TEMPO", fill=COR_TEXTO,
                  font=ImageFont.truetype(FONTE_TITULO, 40))

    linhas = [
        f"Cidade: {info['cidade']}",
        f"País: {info['pais']}",
        f"Temperatura: {formatar_numero(info['temperatura'])} °C",
        f"Sensação: {formatar_numero(info['sensacao'])} °C",
        f"Umidade: {info['umidade']}%",
        f"Clima: {info['clima']}",
    ]
    for i, linha in enumerate(linhas):
        fonte = fonte_que_cabe(desenhar, linha, FONTE_TEXTO, 30)
        desenhar.text((80, 170 + i * 50), linha, fill=COR_TEXTO, font=fonte)

    # 5.2 Salva a imagem dentro da pasta imagens/
    imagem.convert("RGB").save(caminho)


def caminho_do_card(chat_id):
    """Um arquivo por conversa, para duas pessoas ao mesmo tempo não receberem o card uma da outra."""
    return os.path.join(PASTA_IMAGENS, f"clima_{chat_id}.png")


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Olá! Digite o nome de uma cidade para consultar o clima.\n"
        "Exemplo: Blumenau\n\n"
        "Cidades do Brasil têm prioridade. Para outro país, inclua o nome dele. Exemplo: Toledo, Spain",
    )


@bot.message_handler(func=lambda message: True)
def clima(message):
    bot.send_chat_action(message.chat.id, "upload_photo")
    info = buscar_clima(message.text.strip())
    if info is None:
        bot.send_message(message.chat.id, "Não encontrei essa cidade. Confira o nome e tente de novo.")
        return

    caminho = caminho_do_card(message.chat.id)
    gerar_card(info, caminho)
    with open(caminho, "rb") as foto:
        bot.send_photo(message.chat.id, foto)


if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not WEATHER_API_KEY:
        raise SystemExit("Defina as variáveis de ambiente TELEGRAM_TOKEN e WEATHER_API_KEY.")

    # 5.1 Cria a pasta de imagens, caso ainda não exista
    if not os.path.exists(PASTA_IMAGENS):
        os.makedirs(PASTA_IMAGENS)

    log.info("Bot em execução. Pressione Ctrl+C para encerrar.")
    bot.infinity_polling()
