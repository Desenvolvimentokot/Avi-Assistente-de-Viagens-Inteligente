import os
import logging
import requests
import json
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SkyscannerService:
    def __init__(self):
        # Escolher uma das duas credenciais disponíveis
        self.account_sid = "IRHRCerDjfGB6142175YvFpgXdE5wSp6P1"  # Primeira credencial
        self.auth_token = "W_TRSD7aw.iBVsC9HGQvAENiDfihdHLC"
        self.api_version = "14"

        # Segunda credencial disponível como fallback
        self.account_sid_alt = "IRTogmim4RSd6142175V4NQgY4ynvMngL1"
        self.auth_token_alt = "E-UvnxtTNyBQbtgMUE36KURd.sNnQXou"

        self.base_url = "https://partners.api.skyscanner.net/apiservices"
        self.affiliate_id = "flai-travel-assistant"  # ID de afiliado para os links de compra

    def search_flights(self, params):
        """
        Busca voos utilizando a API do Skyscanner

        Parâmetros:
        - params: dicionário contendo parâmetros de busca (origem, destino, datas, etc.)

        Retorno:
        - Dicionário com os resultados da busca
        """
        try:
            # Simulação de resposta para desenvolvimento
            # Em produção, substituir por chamada real à API
            logger.info(f"Buscando voos no Skyscanner com parâmetros: {params}")

            # Dados simulados
            origin = params.get('origin', '')
            destination = params.get('destination', '')
            departure_date = params.get('departure_date', '')
            return_date = params.get('return_date', '')

            # Validar parâmetros mínimos
            if not origin or not destination or not departure_date:
                return {"error": "Parâmetros insuficientes para busca de voos"}

            # Gerar dados simulados para desenvolvimento
            flights = self._generate_simulated_flights(
                origin, 
                destination, 
                departure_date, 
                return_date
            )

            return {"flights": flights}

        except Exception as e:
            logger.error(f"Erro ao buscar voos no Skyscanner: {str(e)}")
            return {"error": f"Erro ao buscar voos: {str(e)}"}

    def get_best_price_options(self, origin, destination, date_range_start, date_range_end):
        """
        Busca as melhores opções de preço para um período específico

        Parâmetros:
        - origin: código IATA do aeroporto de origem
        - destination: código IATA do aeroporto de destino
        - date_range_start: data de início do período (formato YYYY-MM-DD)
        - date_range_end: data de fim do período (formato YYYY-MM-DD)

        Retorno:
        - Dicionário com as melhores opções de preço
        """
        try:
            # Validar parâmetros mínimos
            if not origin or not destination or not date_range_start or not date_range_end:
                return {"error": "Parâmetros insuficientes para busca de melhores preços"}

            # Gerar dados simulados para desenvolvimento
            best_prices = self._generate_simulated_best_prices(
                origin,
                destination,
                date_range_start,
                date_range_end
            )

            return {"best_prices": best_prices}

        except Exception as e:
            logger.error(f"Erro ao buscar melhores preços no Skyscanner: {str(e)}")
            return {"error": f"Erro ao buscar melhores preços: {str(e)}"}

    def _generate_affiliate_link(self, origin, destination, departure_date, return_date=None):
        """
        Gera um link de afiliado para compra das passagens

        Parâmetros:
        - origin: código IATA do aeroporto de origem
        - destination: código IATA do aeroporto de destino
        - departure_date: data de partida (formato YYYY-MM-DD)
        - return_date: data de retorno (formato YYYY-MM-DD)

        Retorno:
        - URL de afiliado do Skyscanner
        """
        base_url = "https://www.skyscanner.com.br/transport/flights"

        # Formatar as datas para o padrão do Skyscanner (YYMMDD)
        try:
            dep_formatted = datetime.strptime(departure_date, "%Y-%m-%d").strftime("%y%m%d")
        except:
            dep_formatted = "231201"  # Data padrão se houver erro

        ret_formatted = ""
        if return_date:
            try:
                ret_formatted = "/" + datetime.strptime(return_date, "%Y-%m-%d").strftime("%y%m%d")
            except:
                ret_formatted = "/231208"  # Data padrão se houver erro

        # Montar a URL
        url = f"{base_url}/{origin}/{destination}/{dep_formatted}{ret_formatted}/?adults=1&adultsv2=1&cabinclass=economy&children=0&inboundaltsenabled=false&infants=0&outboundaltsenabled=false&preferdirects=false&ref=home&rtn={1 if return_date else 0}"

        # Adicionar parâmetro de afiliado
        url += f"&affilid={self.affiliate_id}"

        return url

    def _generate_simulated_flights(self, origin, destination, departure_date, return_date=None):
        """
        Gera dados simulados de voos para desenvolvimento
        """
        airlines = ["LATAM", "GOL", "Azul", "Emirates", "Air France", "British Airways", "American Airlines"]
        flights = []

        # Converter string de data para objeto datetime
        try:
            dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
        except:
            dep_date = datetime.now() + timedelta(days=30)

        # Gerar entre 3 e 8 opções de voo
        import random
        num_options = random.randint(3, 8)

        for i in range(num_options):
            # Escolher horário aleatório entre 05:00 e 23:00
            dep_hour = random.randint(5, 23)
            dep_minute = random.choice([0, 15, 30, 45])

            # Gerar duração aleatória entre 2 e 15 horas
            duration_hours = random.randint(2, 15)
            duration_minutes = random.choice([0, 15, 30, 45])

            # Calcular chegada
            departure_datetime = dep_date.replace(hour=dep_hour, minute=dep_minute)
            arrival_datetime = departure_datetime + timedelta(hours=duration_hours, minutes=duration_minutes)

            # Gerar preço aleatório entre 800 e 5000
            price = random.randint(800, 5000)

            # Escolher companhia aérea
            airline = random.choice(airlines)

            # Gerar link de afiliado
            affiliate_link = self._generate_affiliate_link(
                origin, 
                destination, 
                departure_date, 
                return_date
            )

            # Formar objeto de voo
            flight = {
                "id": f"flight_{i+1}",
                "price": price,
                "currency": "BRL",
                "departure": {
                    "airport": origin,
                    "time": departure_datetime.isoformat()
                },
                "arrival": {
                    "airport": destination,
                    "time": arrival_datetime.isoformat()
                },
                "duration": f"PT{duration_hours}H{duration_minutes}M",
                "segments": random.randint(1, 3),
                "airline": airline,
                "affiliate_link": affiliate_link
            }

            flights.append(flight)

        # Ordenar por preço
        flights.sort(key=lambda x: x["price"])

        return flights

    def _generate_simulated_best_prices(self, origin, destination, date_range_start, date_range_end):
        """
        Gera dados simulados de melhores preços para desenvolvimento
        """
        best_prices = []

        # Converter strings de data para objetos datetime
        try:
            start_date = datetime.strptime(date_range_start, "%Y-%m-%d")
            end_date = datetime.strptime(date_range_end, "%Y-%m-%d")
        except:
            start_date = datetime.now() + timedelta(days=30)
            end_date = start_date + timedelta(days=30)

        # Calcular diferença em dias
        date_diff = (end_date - start_date).days
        if date_diff <= 0:
            date_diff = 30  # Padrão de 30 dias se datas forem inválidas

        # Gerar entre 5 e 10 opções de preço
        import random
        num_options = min(date_diff, random.randint(5, 10))

        # Dividir o período em porções aproximadamente iguais
        day_step = max(1, date_diff // num_options)

        for i in range(num_options):
            # Gerar data dentro do período
            flight_date = start_date + timedelta(days=i * day_step)

            # Gerar preço base entre 800 e 4000
            base_price = random.randint(800, 4000)

            # Adicionar variação para tornar mais realista
            # Os primeiros e últimos tendem a ser mais caros
            if i < 2 or i > num_options - 3:
                price_factor = 1.2
            else:
                price_factor = 0.9

            price = int(base_price * price_factor)

            # Gerar link de afiliado
            affiliate_link = self._generate_affiliate_link(
                origin, 
                destination, 
                flight_date.strftime("%Y-%m-%d")
            )

            # Formar objeto de melhor preço
            best_price = {
                "date": flight_date.isoformat(),
                "price": price,
                "currency": "BRL",
                "affiliate_link": affiliate_link
            }

            best_prices.append(best_price)

        # Ordenar por preço
        best_prices.sort(key=lambda x: x["price"])

        return best_prices