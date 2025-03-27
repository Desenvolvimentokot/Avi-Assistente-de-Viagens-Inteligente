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
            # Extrair parâmetros
            origin = params.get('origin', '')
            destination = params.get('destination', '')
            departure_date = params.get('departure_date', '')
            return_date = params.get('return_date', '')
            adults = params.get('adults', 1)
            currency = params.get('currency', 'BRL')
            
            # Validar parâmetros mínimos
            if not origin or not destination or not departure_date:
                return {"error": "Parâmetros insuficientes para busca de voos"}
                
            logger.info(f"Buscando voos no Skyscanner com parâmetros: {params}")
            
            # Fazer a requisição para a API Skyscanner
            url = f"{self.base_url}/v{self.api_version}/flights/browse/quotes"
            headers = {
                'x-rapidapi-key': self.auth_token,
                'x-rapidapi-host': 'skyscanner-skyscanner-flight-search-v1.p.rapidapi.com',
                'content-type': 'application/json'
            }
            
            query_params = {
                'originPlace': f"{origin}-sky",
                'destinationPlace': f"{destination}-sky",
                'outboundPartialDate': departure_date,
                'inboundPartialDate': return_date,
                'adults': adults,
                'currency': currency
            }
            
            # Tentar fazer a chamada à API real
            response = requests.get(url, headers=headers, params=query_params)
            
            # Se houver erro na API, usar fallback para dados simulados
            if response.status_code != 200:
                logger.warning(f"Erro na API Skyscanner (status {response.status_code}), usando dados de fallback")
                if hasattr(self, '_generate_simulated_flights'):
                    logger.info("Usando dados simulados como fallback")
                    flights = self._generate_simulated_flights(
                        origin, 
                        destination, 
                        departure_date, 
                        return_date
                    )
                    return {"flights": flights, "is_simulated": True}
                else:
                    return {"error": f"Erro na API Skyscanner: {response.status_code} - {response.text}"}
            
            # Processar resultados reais da API
            data = response.json()
            quotes = data.get('Quotes', [])
            carriers = data.get('Carriers', [])
            places = data.get('Places', [])
            
            # Mapear IDs de companhias aéreas para nomes
            carrier_map = {c['CarrierId']: c['Name'] for c in carriers}
            # Mapear IDs de lugares para nomes
            place_map = {p['PlaceId']: p['Name'] for p in places}
            
            # Formatar os resultados para o nosso formato padrão
            flights = []
            for quote in quotes:
                # Extrair informações da cotação
                outbound = quote.get('OutboundLeg', {})
                inbound = quote.get('InboundLeg', {}) if return_date else None
                
                # Obter IDs das companhias
                carrier_ids = outbound.get('CarrierIds', [])
                carrier_id = carrier_ids[0] if carrier_ids else None
                
                # Obter nome da companhia
                airline = carrier_map.get(carrier_id, "Companhia não especificada")
                
                # Criar objeto de voo
                flight = {
                    "id": f"flight_{quote.get('QuoteId')}",
                    "price": quote.get('MinPrice'),
                    "currency": currency,
                    "departure": {
                        "airport": origin,
                        "time": outbound.get('DepartureDate')
                    },
                    "arrival": {
                        "airport": destination,
                        "time": None  # A API de cotações não fornece hora de chegada
                    },
                    "airline": airline,
                    "is_direct": quote.get('Direct', False),
                    "affiliate_link": self._generate_affiliate_link(
                        origin, 
                        destination, 
                        departure_date, 
                        return_date
                    )
                }
                
                flights.append(flight)
            
            # Ordenar por preço
            flights.sort(key=lambda x: x["price"])
            
            return {"flights": flights}

        except Exception as e:
            logger.error(f"Erro ao buscar voos no Skyscanner: {str(e)}")
            # Em caso de falha na API, tentar usar dados simulados como último recurso
            try:
                if hasattr(self, '_generate_simulated_flights'):
                    logger.info("Usando dados simulados como fallback após erro")
                    flights = self._generate_simulated_flights(
                        params.get('origin', ''), 
                        params.get('destination', ''), 
                        params.get('departure_date', ''), 
                        params.get('return_date', '')
                    )
                    return {"flights": flights, "is_simulated": True, "error_message": str(e)}
            except:
                pass
                
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

            logger.info(f"Buscando melhores preços para {origin} -> {destination} entre {date_range_start} e {date_range_end}")
            
            # Fazer a requisição para a API Skyscanner
            url = f"{self.base_url}/v{self.api_version}/flights/browse/calendar"
            headers = {
                'x-rapidapi-key': self.auth_token,
                'x-rapidapi-host': 'skyscanner-skyscanner-flight-search-v1.p.rapidapi.com',
                'content-type': 'application/json'
            }
            
            query_params = {
                'originPlace': f"{origin}-sky",
                'destinationPlace': f"{destination}-sky",
                'outboundPartialDate': date_range_start,
                'inboundPartialDate': date_range_end,
                'currency': 'BRL'
            }
            
            # Tentar fazer a chamada à API real
            response = requests.get(url, headers=headers, params=query_params)
            
            # Se houver erro na API, usar fallback para dados simulados
            if response.status_code != 200:
                logger.warning(f"Erro na API Skyscanner (status {response.status_code}), usando dados de fallback")
                if hasattr(self, '_generate_simulated_best_prices'):
                    logger.info("Usando dados simulados como fallback")
                    best_prices = self._generate_simulated_best_prices(
                        origin, destination, date_range_start, date_range_end
                    )
                    return {"best_prices": best_prices, "is_simulated": True}
                else:
                    return {"error": f"Erro na API Skyscanner: {response.status_code} - {response.text}"}
            
            # Processar resultados reais da API
            data = response.json()
            quotes = data.get('Quotes', [])
            best_prices = []
            
            # Transformar resultados no formato padronizado
            for quote in quotes:
                price = quote.get('MinPrice')
                date = quote.get('OutboundLeg', {}).get('DepartureDate')
                
                # Formatar a data para ISO
                try:
                    formatted_date = date.split('T')[0] if date and 'T' in date else date
                except:
                    formatted_date = date
                
                best_price = {
                    "date": formatted_date,
                    "price": price,
                    "currency": "BRL",
                    "affiliate_link": self._generate_affiliate_link(
                        origin, destination, formatted_date
                    )
                }
                
                best_prices.append(best_price)
            
            # Ordenar por preço
            best_prices.sort(key=lambda x: x["price"])
            
            return {"best_prices": best_prices}

        except Exception as e:
            logger.error(f"Erro ao buscar melhores preços no Skyscanner: {str(e)}")
            # Em caso de falha na API, tentar usar dados simulados como último recurso
            try:
                if hasattr(self, '_generate_simulated_best_prices'):
                    logger.info("Usando dados simulados como fallback após erro")
                    best_prices = self._generate_simulated_best_prices(
                        origin, destination, date_range_start, date_range_end
                    )
                    return {"best_prices": best_prices, "is_simulated": True, "error_message": str(e)}
            except:
                pass
                
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