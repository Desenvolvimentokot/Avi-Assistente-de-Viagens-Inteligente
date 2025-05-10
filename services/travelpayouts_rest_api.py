"""
TravelPayouts REST API Client

Este módulo fornece uma interface direta para a API REST do TravelPayouts,
permitindo buscar voos, preços e outras informações sem depender de Playwright
ou extração de dados de páginas web.

Documentação TravelPayouts API:
- https://support.travelpayouts.com/hc/en-us/articles/115000343268-Aviasales-API
- https://support.travelpayouts.com/hc/en-us/articles/205065377-Travel-insights-API
- https://support.travelpayouts.com/hc/en-us/articles/360000303531-Flight-data-API
"""

import os
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode

# Configurar logger
logger = logging.getLogger(__name__)

class TravelPayoutsRestAPI:
    """
    Cliente para a API REST do TravelPayouts com métodos para buscar dados de voos
    usando as APIs oficiais, sem depender de scraping ou automação de browser.
    """

    def __init__(self):
        """
        Inicializa o cliente da API REST com as credenciais e configurações
        """
        # Credenciais de API
        self.token = os.environ.get("TRAVELPAYOUTS_TOKEN", "04e8b4b773de57b38461673a3dd9b133")
        self.marker = os.environ.get("TRAVELPAYOUTS_MARKER", "620701")
        
        # URLs base para diferentes APIs
        self.data_api_base = "https://api.travelpayouts.com/data"
        self.flights_api_base = "https://api.travelpayouts.com/v1"
        self.aviasales_api_base = "https://api.travelpayouts.com/aviasales"
        
        # Endpoints específicos
        self.prices_latest_endpoint = f"{self.flights_api_base}/prices/latest"
        self.cheap_prices_endpoint = f"{self.flights_api_base}/prices/cheap"
        self.month_matrix_endpoint = f"{self.flights_api_base}/prices/month-matrix"
        self.calendar_prices_endpoint = f"{self.flights_api_base}/prices/calendar"
        self.direct_flights_endpoint = f"{self.data_api_base}/routes.json"
        self.airports_endpoint = f"{self.data_api_base}/airports.json"
        self.airlines_endpoint = f"{self.data_api_base}/airlines.json"
        
        logger.info("TravelPayoutsRestAPI inicializado")
        logger.info(f"API Token configurado: {self.token[:3]}...{self.token[-4:]}")
        logger.info(f"Marker configurado: {self.marker}")

    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1):
        """
        Busca voos usando a API REST TravelPayouts (preços de calendário + preços baratos)
        
        Args:
            origin: código IATA do aeroporto de origem
            destination: código IATA do aeroporto de destino
            departure_date: data de partida no formato YYYY-MM-DD
            return_date: data de retorno no formato YYYY-MM-DD (opcional)
            adults: número de adultos
            
        Returns:
            Lista de ofertas de voos ou lista vazia se não encontrar resultados
        """
        logger.info(f"Buscando voos: {origin} → {destination} | Partida: {departure_date} | Retorno: {return_date}")
        
        # Experimentar várias APIs para encontrar a melhor resposta
        
        # 1. Tentar primeiro com API de calendário para ter visão do mês
        calendar_results = self._search_calendar_prices(origin, destination, departure_date)
        if calendar_results and len(calendar_results) > 0:
            logger.info(f"Encontrados {len(calendar_results)} voos via API de calendário")
            return calendar_results
        
        # 2. Tentar com API de preços baratos como alternativa
        cheap_results = self._search_cheap_prices(origin, destination, departure_date, return_date)
        if cheap_results and len(cheap_results) > 0:
            logger.info(f"Encontrados {len(cheap_results)} voos via API de preços baratos")
            return cheap_results
        
        # 3. Se não tiver resultados, tentar API de melhores preços de mês
        month_matrix_results = self._search_month_matrix(origin, destination, departure_date)
        if month_matrix_results and len(month_matrix_results) > 0:
            logger.info(f"Encontrados {len(month_matrix_results)} voos via API de matriz de mês")
            return month_matrix_results
        
        # 4. Se ainda não encontrou resultados, retornar um resultado para redirecionamento
        logger.warning(f"Nenhum resultado encontrado. Criando link de redirecionamento.")
        return [self._create_redirect_result(origin, destination, departure_date, return_date)]

    def _search_calendar_prices(self, origin, destination, departure_date):
        """
        Busca preços de voos usando a API de calendário
        
        Args:
            origin: código IATA do aeroporto de origem
            destination: código IATA do aeroporto de destino
            departure_date: data de partida no formato YYYY-MM-DD
            
        Returns:
            Lista de voos formatados ou lista vazia
        """
        try:
            # Extrair o mês da data de partida (YYYY-MM)
            departure_month = "-".join(departure_date.split("-")[:2])
            
            # Parâmetros da API
            params = {
                "token": self.token,
                "origin": origin,
                "destination": destination,
                "calendar_type": "departure_date",
                "month": departure_month,
                "currency": "BRL",
                "show_to_affiliates": "true"
            }
            
            # Fazer a requisição
            start_time = time.time()
            response = requests.get(self.calendar_prices_endpoint, params=params)
            elapsed_time = time.time() - start_time
            logger.info(f"Requisição API calendário: {elapsed_time:.2f}s | Status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Erro na API calendário: {response.status_code} - {response.text}")
                return []
            
            # Processar a resposta
            data = response.json()
            if not data.get("success", False):
                logger.error(f"API calendário retornou sucesso=false: {data.get('error', 'Erro desconhecido')}")
                return []
                
            # Processar e formatar os resultados
            flights = []
            raw_data = data.get("data", {})
            
            for date_str, prices in raw_data.items():
                if not prices:
                    continue
                    
                for flight_info in prices:
                    # Verificar se tem preço e outras informações essenciais
                    if not flight_info.get("price"):
                        continue
                    
                    # Mapear os dados para um formato consistente
                    flight = self._format_calendar_flight(
                        flight_info=flight_info, 
                        origin=origin, 
                        destination=destination, 
                        date=date_str
                    )
                    
                    flights.append(flight)
            
            # Ordenar por preço (mais barato primeiro)
            flights.sort(key=lambda f: float(f["price"]["total"]))
            
            # Limitar a 20 resultados para não sobrecarregar
            return flights[:20] if len(flights) > 20 else flights
            
        except Exception as e:
            logger.error(f"Erro ao buscar preços de calendário: {str(e)}")
            return []

    def _search_cheap_prices(self, origin, destination, departure_date, return_date=None):
        """
        Busca preços de voos usando a API de preços baratos
        
        Args:
            origin: código IATA do aeroporto de origem
            destination: código IATA do aeroporto de destino
            departure_date: data de partida no formato YYYY-MM-DD
            return_date: data de retorno no formato YYYY-MM-DD (opcional)
            
        Returns:
            Lista de voos formatados ou lista vazia
        """
        try:
            # Parâmetros da API
            params = {
                "token": self.token,
                "origin": origin,
                "destination": destination,
                "depart_date": departure_date,
                "currency": "BRL",
            }
            
            # Adicionar data de retorno se fornecida
            if return_date:
                params["return_date"] = return_date
            
            # Fazer a requisição
            start_time = time.time()
            response = requests.get(self.cheap_prices_endpoint, params=params)
            elapsed_time = time.time() - start_time
            logger.info(f"Requisição API preços baratos: {elapsed_time:.2f}s | Status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Erro na API preços baratos: {response.status_code} - {response.text}")
                return []
            
            # Processar a resposta
            data = response.json()
            if not data.get("success", False):
                logger.error(f"API preços baratos retornou sucesso=false: {data.get('error', 'Erro desconhecido')}")
                return []
                
            # Processar e formatar os resultados
            flights = []
            raw_data = data.get("data", {}).get(destination, {})
            
            if not raw_data:
                logger.warning(f"Nenhum resultado para {destination} em data.data")
                return []
            
            for date_str, flight_info in raw_data.items():
                # Verificar se tem preço e outras informações essenciais
                if not flight_info.get("price"):
                    continue
                
                # Mapear os dados para um formato consistente
                flight = self._format_cheap_flight(
                    flight_info=flight_info, 
                    origin=origin, 
                    destination=destination, 
                    date=date_str,
                    return_date=return_date
                )
                
                flights.append(flight)
            
            # Ordenar por preço (mais barato primeiro)
            flights.sort(key=lambda f: float(f["price"]["total"]))
            
            # Limitar a 20 resultados para não sobrecarregar
            return flights[:20] if len(flights) > 20 else flights
            
        except Exception as e:
            logger.error(f"Erro ao buscar preços baratos: {str(e)}")
            return []

    def _search_month_matrix(self, origin, destination, departure_date):
        """
        Busca preços de voos usando a API de matriz de mês
        
        Args:
            origin: código IATA do aeroporto de origem
            destination: código IATA do aeroporto de destino
            departure_date: data de partida no formato YYYY-MM-DD
            
        Returns:
            Lista de voos formatados ou lista vazia
        """
        try:
            # Extrair o mês da data de partida (YYYY-MM)
            departure_month = "-".join(departure_date.split("-")[:2])
            
            # Parâmetros da API
            params = {
                "token": self.token,
                "origin": origin,
                "destination": destination,
                "month": departure_month,
                "currency": "BRL",
                "show_to_affiliates": "true"
            }
            
            # Fazer a requisição
            start_time = time.time()
            response = requests.get(self.month_matrix_endpoint, params=params)
            elapsed_time = time.time() - start_time
            logger.info(f"Requisição API matriz mês: {elapsed_time:.2f}s | Status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Erro na API matriz mês: {response.status_code} - {response.text}")
                return []
            
            # Processar a resposta
            data = response.json()
            if not data.get("success", False):
                logger.error(f"API matriz mês retornou sucesso=false: {data.get('error', 'Erro desconhecido')}")
                return []
                
            # Processar e formatar os resultados
            flights = []
            raw_data = data.get("data", [])
            
            for flight_info in raw_data:
                # Verificar se tem preço e outras informações essenciais
                if not flight_info.get("value"):
                    continue
                
                # Extrair data de partida do formato API (YYYY-MM-DD)
                date_str = flight_info.get("depart_date")
                if not date_str:
                    continue
                
                # Mapear os dados para um formato consistente
                flight = self._format_matrix_flight(
                    flight_info=flight_info, 
                    origin=origin, 
                    destination=destination
                )
                
                flights.append(flight)
            
            # Ordenar por preço (mais barato primeiro)
            flights.sort(key=lambda f: float(f["price"]["total"]))
            
            # Limitar a 20 resultados para não sobrecarregar
            return flights[:20] if len(flights) > 20 else flights
            
        except Exception as e:
            logger.error(f"Erro ao buscar matriz de mês: {str(e)}")
            return []

    def _format_calendar_flight(self, flight_info, origin, destination, date):
        """
        Formata um voo da API de calendário para o formato da aplicação
        
        Args:
            flight_info: informações do voo da API
            origin: código IATA de origem
            destination: código IATA de destino
            date: data do voo no formato YYYY-MM-DD
            
        Returns:
            Voo formatado para a aplicação
        """
        # Extrair informações básicas
        price = flight_info.get("price", 0)
        airline = flight_info.get("airline", "")
        flight_number = flight_info.get("flight_number", "")
        
        # Construir URL de reserva
        booking_url = self._create_booking_url(
            origin=origin,
            destination=destination,
            departure_date=date,
            return_date=flight_info.get("return_date")
        )
        
        # Construir segmento de ida
        departure_segment = {
            "departure": {
                "iataCode": origin,
                "at": f"{date}T10:00:00"  # Horário estimado
            },
            "arrival": {
                "iataCode": destination,
                "at": f"{date}T12:00:00"  # Horário estimado
            },
            "carrierCode": airline,
            "number": flight_number,
            "duration": "2:00"  # Duração estimada
        }
        
        # Segmentos de itinerário (ida)
        itineraries = [{
            "segments": [departure_segment]
        }]
        
        # Se tiver data de retorno, adicionar segmento de volta
        if flight_info.get("return_date"):
            return_date = flight_info.get("return_date")
            
            return_segment = {
                "departure": {
                    "iataCode": destination,
                    "at": f"{return_date}T16:00:00"  # Horário estimado
                },
                "arrival": {
                    "iataCode": origin,
                    "at": f"{return_date}T18:00:00"  # Horário estimado
                },
                "carrierCode": airline,
                "number": flight_number,
                "duration": "2:00"  # Duração estimada
            }
            
            itineraries.append({
                "segments": [return_segment]
            })
        
        # Formato final do voo
        return {
            "id": f"TP{flight_info.get('price')}",
            "itineraries": itineraries,
            "price": {
                "total": str(price),
                "currency": "BRL"
            },
            "validatingAirlineCodes": [airline] if airline else ["TP"],
            "source": "TravelPayouts",
            "booking_url": booking_url,
            "number_of_bookings": flight_info.get("number_of_changes", 0)
        }

    def _format_cheap_flight(self, flight_info, origin, destination, date, return_date=None):
        """
        Formata um voo da API de preços baratos para o formato da aplicação
        
        Args:
            flight_info: informações do voo da API
            origin: código IATA de origem
            destination: código IATA de destino
            date: data do voo no formato YYYY-MM-DD
            return_date: data de retorno (opcional)
            
        Returns:
            Voo formatado para a aplicação
        """
        # Extrair informações básicas
        price = flight_info.get("price", 0)
        airline = flight_info.get("airline", "")
        flight_number = flight_info.get("flight_number", "")
        departure_at = flight_info.get("departure_at", date)
        return_at = flight_info.get("return_at", return_date)
        
        # Garantir que temos ao menos a data
        if not departure_at:
            departure_at = date
        
        # Construir URL de reserva
        booking_url = self._create_booking_url(
            origin=origin,
            destination=destination,
            departure_date=departure_at,
            return_date=return_at
        )
        
        # Construir segmento de ida
        departure_time = "10:00"  # Horário estimado
        arrival_time = "12:00"    # Horário estimado
        
        # Se departure_at tiver formato ISO com horário, extrair
        if "T" in departure_at:
            parts = departure_at.split("T")
            departure_at = parts[0]  # Data YYYY-MM-DD
            if len(parts) > 1 and ":" in parts[1]:
                departure_time = parts[1][:5]  # Extrair HH:MM
                
                # Estimar chegada +2h
                arrival_parts = departure_time.split(":")
                arrival_hour = int(arrival_parts[0]) + 2
                arrival_time = f"{arrival_hour:02d}:{arrival_parts[1]}"
        
        departure_segment = {
            "departure": {
                "iataCode": origin,
                "at": f"{departure_at}T{departure_time}:00"
            },
            "arrival": {
                "iataCode": destination,
                "at": f"{departure_at}T{arrival_time}:00"
            },
            "carrierCode": airline,
            "number": flight_number,
            "duration": "2:00"  # Duração estimada
        }
        
        # Segmentos de itinerário (ida)
        itineraries = [{
            "segments": [departure_segment]
        }]
        
        # Se tiver data de retorno, adicionar segmento de volta
        if return_at:
            return_departure_time = "16:00"  # Horário estimado
            return_arrival_time = "18:00"    # Horário estimado
            
            # Se return_at tiver formato ISO com horário, extrair
            if "T" in return_at:
                parts = return_at.split("T")
                return_at = parts[0]  # Data YYYY-MM-DD
                if len(parts) > 1 and ":" in parts[1]:
                    return_departure_time = parts[1][:5]  # Extrair HH:MM
                    
                    # Estimar chegada +2h
                    arrival_parts = return_departure_time.split(":")
                    arrival_hour = int(arrival_parts[0]) + 2
                    return_arrival_time = f"{arrival_hour:02d}:{arrival_parts[1]}"
            
            return_segment = {
                "departure": {
                    "iataCode": destination,
                    "at": f"{return_at}T{return_departure_time}:00"
                },
                "arrival": {
                    "iataCode": origin,
                    "at": f"{return_at}T{return_arrival_time}:00"
                },
                "carrierCode": airline,
                "number": flight_number,
                "duration": "2:00"  # Duração estimada
            }
            
            itineraries.append({
                "segments": [return_segment]
            })
        
        # Formato final do voo
        return {
            "id": f"TP{price}",
            "itineraries": itineraries,
            "price": {
                "total": str(price),
                "currency": "BRL"
            },
            "validatingAirlineCodes": [airline] if airline else ["TP"],
            "source": "TravelPayouts",
            "booking_url": booking_url,
            "number_of_bookings": flight_info.get("number_of_changes", 0),
            "transfers": flight_info.get("transfers", 0)
        }

    def _format_matrix_flight(self, flight_info, origin, destination):
        """
        Formata um voo da API de matriz de mês para o formato da aplicação
        
        Args:
            flight_info: informações do voo da API
            origin: código IATA de origem
            destination: código IATA de destino
            
        Returns:
            Voo formatado para a aplicação
        """
        # Extrair informações básicas
        price = flight_info.get("value", 0)
        departure_date = flight_info.get("depart_date", "")
        return_date = flight_info.get("return_date", "")
        
        # Construir URL de reserva
        booking_url = self._create_booking_url(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date
        )
        
        # Construir segmento de ida
        departure_segment = {
            "departure": {
                "iataCode": origin,
                "at": f"{departure_date}T10:00:00"  # Horário estimado
            },
            "arrival": {
                "iataCode": destination,
                "at": f"{departure_date}T12:00:00"  # Horário estimado
            },
            "carrierCode": "TP",
            "number": "MATRIX",
            "duration": "2:00"  # Duração estimada
        }
        
        # Segmentos de itinerário (ida)
        itineraries = [{
            "segments": [departure_segment]
        }]
        
        # Se tiver data de retorno, adicionar segmento de volta
        if return_date:
            return_segment = {
                "departure": {
                    "iataCode": destination,
                    "at": f"{return_date}T16:00:00"  # Horário estimado
                },
                "arrival": {
                    "iataCode": origin,
                    "at": f"{return_date}T18:00:00"  # Horário estimado
                },
                "carrierCode": "TP",
                "number": "MATRIX",
                "duration": "2:00"  # Duração estimada
            }
            
            itineraries.append({
                "segments": [return_segment]
            })
        
        # Formato final do voo
        return {
            "id": f"TP{price}",
            "itineraries": itineraries,
            "price": {
                "total": str(price),
                "currency": "BRL"
            },
            "validatingAirlineCodes": ["TP"],
            "source": "TravelPayouts",
            "booking_url": booking_url,
            "is_direct": flight_info.get("direct", False)
        }

    def _create_redirect_result(self, origin, destination, departure_date, return_date=None):
        """
        Cria um resultado de redirecionamento quando não há dados disponíveis
        
        Args:
            origin: código IATA de origem
            destination: código IATA de destino
            departure_date: data de partida
            return_date: data de retorno (opcional)
            
        Returns:
            Objeto de voo para redirecionamento
        """
        # Construir URL para widget do TravelPayouts
        redirect_url = self._create_booking_url(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date
        )
        
        # Retornar um resultado de redirecionamento
        return {
            "id": "TP_REDIRECT",
            "itineraries": [{
                "segments": [{
                    "departure": {
                        "iataCode": origin,
                        "at": f"{departure_date}T10:00:00"
                    },
                    "arrival": {
                        "iataCode": destination,
                        "at": f"{departure_date}T12:00:00"
                    },
                    "carrierCode": "TP",
                    "number": "DIR"
                }]
            }],
            "price": {
                "total": "0",  # Preço será mostrado no site de destino
                "currency": "BRL"
            },
            "validatingAirlineCodes": ["TP"],
            "source": "TravelPayouts",
            "booking_url": redirect_url,
            "is_redirect": True,
            "label": "Ver todas as opções de voos"
        }

    def _create_booking_url(self, origin, destination, departure_date, return_date=None):
        """
        Cria URL de redirecionamento para o widget do TravelPayouts
        
        Args:
            origin: código IATA de origem
            destination: código IATA de destino
            departure_date: data de partida
            return_date: data de retorno (opcional)
            
        Returns:
            URL para redirecionamento
        """
        base_url = "https://www.travelpayouts.com/flight_search/widget_redirect/"
        
        # Parâmetros mínimos
        params = {
            "marker": self.marker,
            "origin": origin,
            "destination": destination,
            "departure_at": departure_date,
            "locale": "pt",
            "currency": "BRL",
            "one_way": "false" if return_date else "true"
        }
        
        # Adicionar data de retorno se fornecida
        if return_date:
            params["return_at"] = return_date
            
        # Encodar parâmetros e construir URL
        encoded_params = urlencode(params)
        return f"{base_url}?{encoded_params}"

    def get_nearby_airports(self, city_code, max_distance=100):
        """
        Busca aeroportos próximos a uma cidade/aeroporto
        
        Args:
            city_code: código IATA de cidade ou aeroporto
            max_distance: distância máxima em km (padrão: 100)
            
        Returns:
            Lista de aeroportos próximos
        """
        try:
            # Obter dados de aeroportos da TravelPayouts
            response = requests.get(self.airports_endpoint)
            
            if response.status_code != 200:
                logger.error(f"Erro ao buscar aeroportos: {response.status_code}")
                return []
            
            all_airports = response.json()
            nearby = []
            
            # Encontrar o aeroporto de referência
            reference_airport = None
            for airport in all_airports:
                if airport.get("code") == city_code:
                    reference_airport = airport
                    break
            
            if not reference_airport:
                logger.error(f"Aeroporto de referência {city_code} não encontrado")
                return []
            
            # Buscar aeroportos próximos
            ref_lat = float(reference_airport.get("lat", 0))
            ref_lon = float(reference_airport.get("lon", 0))
            
            for airport in all_airports:
                # Pular aeroportos sem coordenadas
                if not airport.get("lat") or not airport.get("lon"):
                    continue
                
                # Pular o próprio aeroporto de referência
                if airport.get("code") == city_code:
                    continue
                
                try:
                    # Calcular distância aproximada (cálculo simplificado)
                    lat = float(airport.get("lat", 0))
                    lon = float(airport.get("lon", 0))
                    
                    dlat = lat - ref_lat
                    dlon = lon - ref_lon
                    
                    # Fórmula de distância simplificada (aproximação para curtas distâncias)
                    distance = (dlat**2 + dlon**2)**0.5 * 111  # 1 grau ≈ 111 km
                    
                    if distance <= max_distance:
                        airport["distance"] = int(distance)
                        nearby.append(airport)
                except Exception as e:
                    logger.error(f"Erro ao calcular distância para {airport.get('code')}: {str(e)}")
                    continue
            
            # Ordenar por distância
            nearby.sort(key=lambda x: x.get("distance", 999))
            
            return nearby
            
        except Exception as e:
            logger.error(f"Erro ao buscar aeroportos próximos: {str(e)}")
            return []

    def get_direct_flights(self, origin):
        """
        Busca destinos com voos diretos a partir de uma origem
        
        Args:
            origin: código IATA de aeroporto de origem
            
        Returns:
            Lista de destinos com voos diretos
        """
        try:
            # Obter dados de rotas diretas da TravelPayouts
            response = requests.get(self.direct_flights_endpoint)
            
            if response.status_code != 200:
                logger.error(f"Erro ao buscar rotas diretas: {response.status_code}")
                return []
            
            routes = response.json()
            direct_destinations = []
            
            # Filtrar rotas a partir da origem especificada
            for route in routes:
                if route.get("origin") == origin and route.get("destination"):
                    # Verificar se esse destino já está na lista
                    destination = route.get("destination")
                    if not any(dest["code"] == destination for dest in direct_destinations):
                        direct_destinations.append({
                            "code": destination,
                            "airline": route.get("airline"),
                            "flights_per_week": route.get("flights_per_week", 0)
                        })
            
            # Ordenar por número de voos por semana (mais frequentes primeiro)
            direct_destinations.sort(key=lambda x: x.get("flights_per_week", 0), reverse=True)
            
            return direct_destinations
            
        except Exception as e:
            logger.error(f"Erro ao buscar voos diretos: {str(e)}")
            return []

# Instanciar o cliente da API REST
travelpayouts_api = TravelPayoutsRestAPI()