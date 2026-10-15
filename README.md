# Bot de clima para Telegram

Bot do Telegram em **Python** que recebe o nome de uma cidade, consulta o clima atual na **WeatherAPI** e responde com um **card em imagem** gerado na hora com o Pillow. Foi um trabalho individual do curso **Python para Inteligência Artificial** do **Entra21** (Blusoft e ACATE), em 2026.

> **English:** Telegram bot written in Python (Entra21 Python for AI course, 2026) that looks up the current weather for a city through WeatherAPI and replies with an image card rendered with Pillow. Brazilian cities take priority, numbers use the Brazilian format and the code has unit tests with mocked API responses.

<img src="docs/exemplo-card.png" alt="Card de exemplo" width="400">

*Card gerado pelo código do bot, com dados de demonstração.*

## O que o enunciado pedia

| Requisito | Como foi atendido |
|---|---|
| `/start` com boas-vindas e instruções | Mensagem com exemplo de uso |
| Consulta HTTP à WeatherAPI e leitura do JSON | `requests` com tempo limite e tratamento de erro |
| Card com cidade, país, temperatura, sensação, umidade e clima | Desenhado com Pillow sobre uma imagem de fundo |
| Envio automático da imagem | `send_photo` logo depois de gerar o card |
| Criar a pasta `imagens/` se não existir | `os.makedirs` ao iniciar o bot |
| Salvar o card em `imagens/` e apagar o anterior | `os.path.exists` e `os.remove` antes de cada card |

## Como funciona

1. O usuário envia `/start` e recebe as instruções de uso.
2. Ao enviar o nome de uma cidade, o bot procura o local na WeatherAPI e **dá preferência a cidades do Brasil**. Sem isso, "Toledo" seria Toledo, nos Estados Unidos, e não Toledo, no Paraná. Para outro país, basta digitar junto, por exemplo `Toledo, Spain`.
3. O bot consulta o clima atual e lê a cidade, o país, a temperatura, a sensação térmica, a umidade e a condição do tempo.
4. O Pillow desenha o card sobre a imagem de fundo, com os números no formato brasileiro (15,1 °C) e o país em português. Se um texto for longo demais, a fonte diminui para caber no painel.
5. O card é salvo na pasta `imagens/`, com um arquivo para cada conversa, e enviado ao usuário. Antes de cada novo card, o arquivo anterior daquela conversa é apagado.

Se a cidade não existir ou a API não responder, o bot avisa o usuário em vez de travar, e o erro fica registrado no log.

## Tecnologias

| Biblioteca | Uso |
|---|---|
| `pyTelegramBotAPI` | Recebe as mensagens e envia texto e imagem pelo Telegram |
| `requests` | Faz as consultas à WeatherAPI |
| `Pillow` | Gera o card com o texto sobre a imagem de fundo |
| `os` | Lê as chaves das variáveis de ambiente, cria a pasta `imagens/` e remove o card anterior |
| `unittest` | Testes automatizados, com as respostas da API simuladas |

## Como rodar

1. Crie um bot com o [@BotFather](https://t.me/BotFather) no Telegram e guarde o token.
2. Crie uma conta gratuita na [WeatherAPI](https://www.weatherapi.com/) e gere uma chave de API.
3. Instale as dependências.
   ```bash
   pip install -r requirements.txt
   ```
4. Defina as chaves como variáveis de ambiente e rode o bot.

   **Linux ou macOS**
   ```bash
   export TELEGRAM_TOKEN="seu_token_do_telegram"
   export WEATHER_API_KEY="sua_chave_da_weatherapi"
   python main.py
   ```

   **Windows (PowerShell)**
   ```powershell
   $env:TELEGRAM_TOKEN="seu_token_do_telegram"
   $env:WEATHER_API_KEY="sua_chave_da_weatherapi"
   python main.py
   ```

As chaves nunca ficam no código, por isso o repositório pode ser público sem expor nenhuma credencial.

## Testes

```bash
python -m unittest discover -s tests -v
```

São 9 testes que rodam sem internet: formatação dos números, preferência por cidades do Brasil, tradução do país, cidade inexistente, geração do card, ajuste de fonte para textos longos e um arquivo por conversa.

## Estrutura

```
bot-clima-telegram/
├── main.py            # código do bot
├── fundo.png          # imagem de fundo do card
├── fontes/            # fonte Liberation Serif (licença SIL OFL)
├── tests/             # testes automatizados
├── docs/              # imagem de exemplo
├── requirements.txt
└── imagens/           # criada automaticamente para os cards gerados
```

## O que eu faria diferente hoje

Revisei o código depois da entrega. Tirei as chaves que estavam escritas no código e passei a lê-las de variáveis de ambiente. Também acrescentei a preferência por cidades do Brasil, um card por conversa, o ajuste da fonte e os testes. Ainda daria para melhorar:

- **Previsão dos próximos dias.** A WeatherAPI também tem o endpoint `forecast.json`, que permitiria mostrar a previsão no card.
- **Ícone do tempo.** A resposta da API traz um ícone para cada condição, que poderia ir no card.
- **Card só em memória.** O enunciado pedia salvar o arquivo em disco. Fora dessa exigência, a imagem poderia ser gerada e enviada direto da memória, sem gravar arquivo.

---

Desenvolvido por **Isadora Fernanda Zappe Schmidt** · [LinkedIn](https://www.linkedin.com/in/isadora-fernanda)
