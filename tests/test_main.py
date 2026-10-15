"""Testes do bot sem acessar a internet: as respostas da WeatherAPI são simuladas."""

import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402


def resposta_falsa(status, dados):
    falsa = mock.Mock(status_code=status)
    falsa.json.return_value = dados
    falsa.raise_for_status.return_value = None
    return falsa


CLIMA_TOLEDO_PR = {
    "location": {"name": "Toledo", "country": "Brazil"},
    "current": {"temp_c": 15.1, "feelslike_c": 15.0, "humidity": 51,
                "condition": {"text": "Sol"}},
}


class FormatacaoTests(unittest.TestCase):
    def test_numero_inteiro_sem_casa_decimal(self):
        self.assertEqual(main.formatar_numero(18.0), "18")

    def test_numero_com_virgula(self):
        self.assertEqual(main.formatar_numero(15.1), "15,1")


class BuscaTests(unittest.TestCase):
    def test_prefere_cidade_do_brasil(self):
        busca = [
            {"name": "Toledo", "country": "United States of America", "lat": 41.65, "lon": -83.54},
            {"name": "Toledo", "country": "Brazil", "lat": -24.72, "lon": -53.74},
        ]
        with mock.patch.object(main.requests, "get", return_value=resposta_falsa(200, busca)):
            self.assertEqual(main.escolher_local("Toledo"), "-24.72,-53.74")

    def test_respeita_pais_digitado(self):
        with mock.patch.object(main.requests, "get") as get:
            self.assertEqual(main.escolher_local("Toledo, Spain"), "Toledo, Spain")
            get.assert_not_called()

    def test_traduz_pais(self):
        respostas = [resposta_falsa(200, []), resposta_falsa(200, CLIMA_TOLEDO_PR)]
        with mock.patch.object(main.requests, "get", side_effect=respostas):
            info = main.buscar_clima("Toledo")
        self.assertEqual(info["pais"], "Brasil")
        self.assertEqual(info["clima"], "Sol")

    def test_cidade_inexistente(self):
        respostas = [resposta_falsa(200, []), resposta_falsa(400, {"error": {}})]
        with mock.patch.object(main.requests, "get", side_effect=respostas):
            self.assertIsNone(main.buscar_clima("Cidadequenaoexiste"))


class CardTests(unittest.TestCase):
    def test_gera_card_e_substitui_o_anterior(self):
        info = {"cidade": "Toledo", "pais": "Brasil", "temperatura": 15.1,
                "sensacao": 15.0, "umidade": 51, "clima": "Sol"}
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "clima_1.png")
            with open(caminho, "w") as antigo:
                antigo.write("arquivo antigo")
            main.gerar_card(info, caminho)
            with open(caminho, "rb") as gerado:
                self.assertEqual(gerado.read(8), b"\x89PNG\r\n\x1a\n")

    def test_texto_longo_cabe_no_painel(self):
        from PIL import Image, ImageDraw
        desenhar = ImageDraw.Draw(Image.new("RGB", (800, 600)))
        texto = "Clima: Possibilidade de chuva irregular com trovoadas"
        fonte = main.fonte_que_cabe(desenhar, texto, main.FONTE_TEXTO, 30)
        self.assertLessEqual(desenhar.textlength(texto, font=fonte), main.LARGURA_MAXIMA_TEXTO)

    def test_um_arquivo_por_conversa(self):
        self.assertNotEqual(main.caminho_do_card(1), main.caminho_do_card(2))


if __name__ == "__main__":
    unittest.main()
