"""
Serviço para integração com a API TravelPayouts
Este módulo fornece métodos para acessar os dados de voos, preços e outros recursos
da API TravelPayouts, formatando as respostas para serem compatíveis com o sistema Flai.

Documentação TravelPayouts:
- https://support.travelpayouts.com/hc/en-us/articles/25289759198226-API-for-Travelpayouts-partner-links 
- https://support.travelpayouts.com/hc/en-us/categories/200358578
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
import random

logger = logging.getLogger(__name__)

class TravelPayoutsService:
    """
    Serviço para interação com a API TravelPayouts
    """
    
    def __init__(self):
        """
        Inicializa o serviço com as credenciais da API
        """
        # Credenciais de API
        self.token = os.environ.get("TRAVELPAYOUTS_TOKEN", "04e8b4b773de57b38461673a3dd9b133")
        self.marker = os.environ.get("TRAVELPAYOUTS_MARKER", "620701")
        
        # URLs base para diferentes APIs
        self.data_api_base = "https://api.travelpayouts.com/data"
        self.flights_api_base = "https://api.travelpayouts.com/v1"
        self.aviasales_api_base = "https://api.travelpayouts.com/aviasales"
        self.partner_api_base = "https://www.travelpayouts.com/widgets/api"
        
        # Endpoints específicos
        self.prices_latest_endpoint = f"{self.flights_api_base}/prices/latest"
        self.cheap_prices_endpoint = f"{self.flights_api_base}/prices/cheap"
        self.month_matrix_endpoint = f"{self.flights_api_base}/prices/month-matrix"
        self.calendar_prices_endpoint = f"{self.flights_api_base}/prices/calendar"
        self.airports_endpoint = f"{self.data_api_base}/airports.json"
        self.airlines_endpoint = f"{self.data_api_base}/airlines.json"
        
        # Informações de inicialização
        logger.info("TravelPayoutsService inicializado")
        logger.info(f"API Token configurado: {self.token[:3]}...{self.token[-4:]}")
        logger.info(f"Marker configurado: {self.marker}")

    def search_flights(self, params):
        """
        Busca voos usando a API do TravelPayouts
        
        Args:
            params: dicionário com parâmetros como:
                - originLocationCode: código IATA da origem
                - destinationLocationCode: código IATA do destino
                - departureDate: data de partida em YYYY-MM-DD
                - returnDate: data de retorno (opcional)
                - adults: número de adultos
                
        Returns:
            Lista de ofertas de voos no formato compatível com a aplicação
        """
        # Validar parâmetros essenciais
        if not params.get('originLocationCode') or not params.get('destinationLocationCode'):
            logger.error("Parâmetros de origem e destino são obrigatórios")
            return []
            
        origin = params.get('originLocationCode')
        destination = params.get('destinationLocationCode')
        
        # Verificar a data de partida
        departure_date = params.get('departureDate')
        if not departure_date:
            # Se não tiver data específica, usar período próximo (30 dias)
            today = datetime.now()
            next_month = today + timedelta(days=30)
            departure_date = next_month.strftime('%Y-%m-%d')
            
        # Extrair o mês da data de partida para o calendário (YYYY-MM)
        try:
            departure_month = "-".join(departure_date.split("-")[:2])  # YYYY-MM
        except:
            departure_month = datetime.now().strftime('%Y-%m')  # Mês atual como fallback
        
        # Formatar parâmetros para API do TravelPayouts (usando API de calendário)
        request_params = {
            "token": self.token,
            "origin": origin,
            "destination": destination,
            "calendar_type": "departure_date",
            "month": departure_month,
            "currency": "BRL",
            "show_to_affiliates": "true"
        }
        
        try:
            # Buscar no endpoint de calendário - este endpoint é mais estável e fornece mais dados
            logger.info(f"Buscando voos de {origin} para {destination} no mês {departure_month}")
            response = requests.get(self.calendar_prices_endpoint, params=request_params)
            
            if response.status_code != 200:
                logger.error(f"Erro na API do TravelPayouts (calendário): {response.status_code} - {response.text}")
                # Tentar alternativa com endpoint de preços baratos
                return self._search_flights_cheap_alternative(origin, destination, departure_date, params.get('returnDate'))
                
            raw_data = response.json()
            
            if not raw_data.get('success', False):
                logger.error(f"API retornou sucesso=false: {raw_data.get('error', 'Erro desconhecido')}")
                return self._search_flights_cheap_alternative(origin, destination, departure_date, params.get('returnDate'))
            
            # Processar e formatar os resultados do calendário
            formatted_results = self._format_calendar_results(raw_data, origin, destination, departure_date)
            
            logger.info(f"Resultados encontrados: {len(formatted_results)} voos")
            
            # Se não encontramos resultados, tentar alternativa
            if len(formatted_results) == 0:
                return self._search_flights_cheap_alternative(origin, destination, departure_date, params.get('returnDate'))
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Erro ao buscar voos (calendário): {str(e)}")
            # Tentar alternativa com endpoint de preços baratos
            return self._search_flights_cheap_alternative(origin, destination, departure_date, params.get('returnDate'))
    
    def _search_flights_cheap_alternative(self, origin, destination, departure_date, return_date=None):
        """
        Método alternativo de busca usando a API de preços baratos
        """
        logger.info(f"Tentando alternativa com API de preços baratos para {origin}-{destination}")
        
        # Formatar parâmetros para API do TravelPayouts (formato da API de Preços Baratos)
        request_params = {
            "token": self.token,
            "origin": origin,
            "destination": destination,
            "depart_date": departure_date,
            "currency": "BRL",
        }
        
        # Adicionar data de retorno se fornecida
        if return_date:
            request_params["return_date"] = return_date
        
        try:
            # Buscar no endpoint de preços baratos
            response = requests.get(self.cheap_prices_endpoint, params=request_params)
            
            if response.status_code != 200:
                logger.error(f"Erro na API alternativa: {response.status_code} - {response.text}")
                return self._create_redirect_flight(origin, destination, departure_date, return_date)
                
            raw_data = response.json()
            
            # Processar e formatar os resultados
            formatted_results = self._format_flight_results(raw_data, origin, destination)
            
            if len(formatted_results) == 0:
                return self._create_redirect_flight(origin, destination, departure_date, return_date)
                
            logger.info(f"Resultados alternativos encontrados: {len(formatted_results)} voos")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Erro ao buscar voos (alternativa): {str(e)}")
            return self._create_redirect_flight(origin, destination, departure_date, return_date)
    
    def _create_redirect_flight(self, origin, destination, departure_date, return_date=None):
        """
        Último recurso: criar um resultado de redirecionamento para o widget de busca do TravelPayouts
        """
        logger.info("Criando resultado de redirecionamento para widget TravelPayouts")
        
        # Gerar link de redirecionamento
        redirect_url = self.get_partner_link(origin, destination, departure_date, return_date)
        
        # Criar um único resultado de redirecionamento
        redirect_flight = {
            'id': "TP_REDIRECT",
            'itineraries': [{
                'segments': [{
                    'departure': {
                        'iataCode': origin,
                        'at': f"{departure_date}T10:00:00"
                    },
                    'arrival': {
                        'iataCode': destination,
                        'at': f"{departure_date}T12:00:00"
                    },
                    'carrierCode': "TP",
                    'number': "REF"
                }]
            }],
            'price': {
                'total': "0", # Preço será mostrado na página de redirecionamento
                'currency': 'BRL'
            },
            'validatingAirlineCodes': ["TP"],
            'source': 'TravelPayouts',
            'redirect_url': redirect_url,
            'is_redirect': True,
            'label': "Ver todas as opções de voos"
        }
        
        return [redirect_flight]
    
    def _format_flight_results(self, api_response, origin, destination):
        """
        Converte a resposta da API do TravelPayouts para o formato usado pela aplicação
        
        Args:
            api_response: Resposta da API do TravelPayouts
            origin: Código IATA de origem
            destination: Código IATA de destino
            
        Returns:
            Lista de voos formatada compatível com a estrutura existente
        """
        formatted_results = []
        
        # A resposta tem formato { "success": true, "data": { "DESTINATION": { "DEPARTURE_DATE": { "price": X, "airline": Y, ... } } } }
        if not api_response.get('success'):
            logger.error("API retornou sucesso=false")
            return []
            
        data = api_response.get('data', {}).get(destination, {})
        
        # ID para os voos
        flight_id_counter = 1
        
        # Processar cada data de partida nos resultados
        for depart_date, flight_info in data.items():
            # Verificar se temos as informações mínimas necessárias
            if 'price' not in flight_info or 'airline' not in flight_info:
                continue
                
            # Informações de voo
            price = flight_info.get('price')
            airline = flight_info.get('airline')
            flight_number = flight_info.get('flight_number', '')
            
            # Construir horários estimados (a API de preços baratos não fornece horários específicos)
            # Podemos usar horários fictícios para demonstração ou obter de outra API
            departure_date = depart_date
            departure_time = "10:00" # Horário estimado
            departure_datetime = f"{departure_date}T{departure_time}:00"
            
            # Para chegada, estimar +2h ou +4h dependendo da distância
            arrival_time = "12:00" if len(origin) == 3 and len(destination) == 3 else "14:00"
            arrival_datetime = f"{departure_date}T{arrival_time}:00"
            
            # Criar segmento de voo
            segment = {
                'departure': {
                    'iataCode': origin,
                    'at': departure_datetime
                },
                'arrival': {
                    'iataCode': destination,
                    'at': arrival_datetime
                },
                'carrierCode': airline,
                'number': flight_number
            }
            
            # Estrutura de itinerário (ida)
            itinerary = {
                'segments': [segment]
            }
            
            # Se tiver data de retorno
            return_itinerary = None
            if flight_info.get('return_date'):
                return_date = flight_info.get('return_date')
                # Horários estimados para o retorno
                return_departure_time = "15:00"
                return_departure_datetime = f"{return_date}T{return_departure_time}:00"
                return_arrival_time = "17:00"
                return_arrival_datetime = f"{return_date}T{return_arrival_time}:00"
                
                return_segment = {
                    'departure': {
                        'iataCode': destination,
                        'at': return_departure_datetime
                    },
                    'arrival': {
                        'iataCode': origin,
                        'at': return_arrival_datetime
                    },
                    'carrierCode': airline,
                    'number': flight_number
                }
                
                return_itinerary = {
                    'segments': [return_segment]
                }
            
            # Montar objeto completo de voo no formato compatível com a aplicação
            formatted_flight = {
                'id': f"TP{flight_id_counter}",
                'itineraries': [itinerary] if not return_itinerary else [itinerary, return_itinerary],
                'price': {
                    'total': str(price),
                    'currency': 'BRL'
                },
                'validatingAirlineCodes': [airline],
                'source': 'TravelPayouts'
            }
            
            formatted_results.append(formatted_flight)
            flight_id_counter += 1
        
        return formatted_results
    
    def _format_calendar_results(self, api_response, origin, destination, target_date=None):
        """
        Formata os resultados da API de calendário para o formato usado pela aplicação
        
        Args:
            api_response: Resposta da API de calendário do TravelPayouts
            origin: Código IATA de origem
            destination: Código IATA de destino
            target_date: Data alvo para filtragem (opcional)
            
        Returns:
            Lista de voos formatados
        """
        formatted_results = []
        
        # Verificar se temos dados válidos
        if not api_response.get('success'):
            logger.error(f"API calendário retornou sucesso=false: {api_response.get('error', 'Erro desconhecido')}")
            return []
        
        # Extrair dados
        data = api_response.get('data', [])
        if not data:
            logger.error("API calendário retornou dados vazios")
            return []
            
        # ID para os voos
        flight_id_counter = 1
        
        # Filtrar resultados pela data alvo, se fornecida
        filtered_data = data
        if target_date:
            filtered_data = [entry for entry in data if entry.get('departure_at', '').startswith(target_date)]
            
            # Se não encontrar nada para a data específica, usar todas as datas
            if not filtered_data:
                filtered_data = data
        
        # Ordenar por preço (mais barato primeiro)
        sorted_data = sorted(filtered_data, key=lambda x: float(x.get('value', 9999999)))
        
        # Limitar a 5 resultados para não sobrecarregar
        limited_data = sorted_data[:5]
        
        # Processar cada entrada
        for entry in limited_data:
            # Extrair informações básicas
            price = entry.get('value')
            airline = entry.get('airline')
            flight_number = f"{airline}{entry.get('flight_number', '')}"
            
            # Datas e horários
            departure_at = entry.get('departure_at')
            return_at = entry.get('return_at')
            
            # Verificar se temos o mínimo necessário
            if not price or not airline or not departure_at:
                continue
                
            # Formatar as datas para o formato esperado
            try:
                # A API retorna datas em formato ISO, mas precisamos garantir
                if 'T' not in departure_at:
                    departure_at = f"{departure_at}T10:00:00"
                    
                if return_at and 'T' not in return_at:
                    return_at = f"{return_at}T15:00:00"
            except:
                # Em caso de erro, usar valores padrão
                departure_at = f"{datetime.now().strftime('%Y-%m-%d')}T10:00:00"
                if return_at:
                    return_date_obj = datetime.now() + timedelta(days=7)
                    return_at = f"{return_date_obj.strftime('%Y-%m-%d')}T15:00:00"
            
            # Calcular hora de chegada (2 horas depois da partida)
            try:
                departure_dt = datetime.fromisoformat(departure_at.replace('Z', '+00:00'))
                arrival_dt = departure_dt + timedelta(hours=2)
                arrival_at = arrival_dt.isoformat()
            except:
                # Fallback para 2 horas depois em formato texto
                arrival_parts = departure_at.split('T')
                hour_parts = arrival_parts[1].split(':')
                arrival_hour = str(int(hour_parts[0]) + 2).zfill(2)
                arrival_at = f"{arrival_parts[0]}T{arrival_hour}:{hour_parts[1]}:{hour_parts[2]}"
            
            # Criar segmento de voo (ida)
            segment = {
                'departure': {
                    'iataCode': origin,
                    'at': departure_at
                },
                'arrival': {
                    'iataCode': destination,
                    'at': arrival_at
                },
                'carrierCode': airline,
                'number': flight_number.replace(airline, '')
            }
            
            # Estrutura de itinerário (ida)
            itinerary = {
                'segments': [segment]
            }
            
            # Se tiver voo de retorno
            return_itinerary = None
            if return_at:
                # Calcular hora de chegada do retorno (2 horas depois da partida do retorno)
                try:
                    return_dt = datetime.fromisoformat(return_at.replace('Z', '+00:00'))
                    return_arrival_dt = return_dt + timedelta(hours=2)
                    return_arrival_at = return_arrival_dt.isoformat()
                except:
                    # Fallback para 2 horas depois em formato texto
                    return_parts = return_at.split('T')
                    return_hour_parts = return_parts[1].split(':')
                    return_arrival_hour = str(int(return_hour_parts[0]) + 2).zfill(2)
                    return_arrival_at = f"{return_parts[0]}T{return_arrival_hour}:{return_hour_parts[1]}:{return_hour_parts[2]}"
                
                return_segment = {
                    'departure': {
                        'iataCode': destination,
                        'at': return_at
                    },
                    'arrival': {
                        'iataCode': origin,
                        'at': return_arrival_at
                    },
                    'carrierCode': airline,
                    'number': flight_number.replace(airline, '')
                }
                
                return_itinerary = {
                    'segments': [return_segment]
                }
            
            # Montar objeto completo de voo
            formatted_flight = {
                'id': f"TP{flight_id_counter}",
                'itineraries': [itinerary] if not return_itinerary else [itinerary, return_itinerary],
                'price': {
                    'total': str(price),
                    'currency': 'BRL'
                },
                'validatingAirlineCodes': [airline],
                'source': 'TravelPayouts'
            }
            
            formatted_results.append(formatted_flight)
            flight_id_counter += 1
        
        return formatted_results
    
    def search_best_prices(self, origin, destination, depart_date=None, return_date=None):
        """
        Busca os melhores preços de voos entre origem e destino
        
        Args:
            origin: Código IATA do local de origem
            destination: Código IATA do local de destino
            depart_date: Data de partida no formato YYYY-MM (opcional)
            return_date: Data de retorno no formato YYYY-MM (opcional)
            
        Returns:
            Lista de preços encontrados
        """
        # Usar a API de matriz de mês para obter preços para todo o mês
        request_params = {
            "token": self.token,
            "origin": origin,
            "destination": destination,
            "currency": "BRL",
        }
        
        # Adicionar datas se fornecidas (formato YYYY-MM)
        if depart_date:
            request_params["month"] = depart_date
            
        try:
            response = requests.get(self.month_matrix_endpoint, params=request_params)
            
            if response.status_code != 200:
                logger.error(f"Erro na API do TravelPayouts (matriz de mês): {response.status_code}")
                return []
                
            result = response.json()
            
            if not result.get('success'):
                logger.error("API de matriz de mês retornou sucesso=false")
                return []
                
            # Extrair os dados de preços
            price_data = result.get('data', [])
            
            # Formatar os resultados
            formatted_prices = []
            for price_entry in price_data:
                formatted_prices.append({
                    'origin': origin,
                    'destination': destination,
                    'departure_date': price_entry.get('depart_date'),
                    'return_date': price_entry.get('return_date'),
                    'price': price_entry.get('value'),
                    'airline': price_entry.get('airline'),
                    'flight_number': price_entry.get('flight_number')
                })
                
            return formatted_prices
            
        except Exception as e:
            logger.error(f"Erro ao buscar melhores preços: {str(e)}")
            return []
    
    def get_partner_link(self, origin, destination, departure_date=None, return_date=None):
        """
        Gera um link de parceiro para redirecionamento para resultados de busca
        
        Args:
            origin: Código IATA do local de origem
            destination: Código IATA do local de destino
            departure_date: Data de partida no formato YYYY-MM-DD (opcional)
            return_date: Data de retorno no formato YYYY-MM-DD (opcional)
            
        Returns:
            String com o URL para redirecionamento
        """
        base_url = "https://www.travelpayouts.com/flight_search/widget_redirect/"
        
        # Parâmetros mínimos
        params = {
            "marker": self.marker,
            "origin": origin,
            "destination": destination,
            "locale": "pt",
            "currency": "BRL",
        }
        
        # Adicionar datas se fornecidas
        if departure_date:
            params["departure_at"] = departure_date
        if return_date:
            params["return_at"] = return_date
            
        # Encodar parâmetros e construir URL
        encoded_params = urlencode(params)
        redirect_url = f"{base_url}?{encoded_params}"
        
        return redirect_url
        
    def get_airports(self):
        """
        Recupera a lista de aeroportos do TravelPayouts
        
        Returns:
            Lista de aeroportos com informações
        """
        try:
            response = requests.get(self.airports_endpoint)
            
            if response.status_code != 200:
                logger.error(f"Erro ao obter aeroportos: {response.status_code}")
                return []
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao obter aeroportos: {str(e)}")
            return []
            
    def get_airlines(self):
        """
        Recupera a lista de companhias aéreas do TravelPayouts
        
        Returns:
            Lista de companhias aéreas com informações
        """
        try:
            response = requests.get(self.airlines_endpoint)
            
            if response.status_code != 200:
                logger.error(f"Erro ao obter companhias aéreas: {response.status_code}")
                return []
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao obter companhias aéreas: {str(e)}")
            return []