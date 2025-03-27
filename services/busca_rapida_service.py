import os
import json
import logging
import re
from datetime import datetime, timedelta
from services.openai_service import OpenAIService
from services.skyscanner_service import SkyscannerService
from services.prompts import BUSCA_RAPIDA_PROMPT

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instanciar serviços
openai_service = OpenAIService()
skyscanner_service = SkyscannerService()

def process_message(message, history=None):
    """
    Processa uma mensagem do usuário no modo busca rápida

    Args:
        message (str): Mensagem do usuário
        history (list): Histórico de mensagens anteriores

    Returns:
        dict: Resposta processada
    """
    if history is None:
        history = []

    try:
        logger.info(f"Processando mensagem no modo busca rápida: {message[:50]}...")

        # Preparar o contexto específico para busca rápida
        system_context = BUSCA_RAPIDA_PROMPT

        # Extrair informações de viagem da mensagem e histórico
        travel_info = extract_travel_info(message, history)
        logger.info(f"Informações de viagem extraídas: {travel_info}")

        # Se temos informações suficientes para fazer uma busca, adicionar ao contexto
        additional_context = ""
        flight_data = None
        best_prices_data = None

        if is_ready_for_search(travel_info):
            logger.info("Informações suficientes para busca encontradas")
            
            # Buscar voos específicos se temos datas específicas
            if travel_info.get('departure_date') and not travel_info.get('is_flexible'):
                logger.info(f"Buscando voos para data específica: {travel_info['departure_date']}")
                flight_data = search_flights(travel_info)
                logger.info(f"Resultados da busca de voos: {flight_data.keys() if isinstance(flight_data, dict) else 'Nenhum'}")

                if 'error' not in flight_data:
                    flights = flight_data.get('flights', [])
                    is_simulated = flight_data.get('is_simulated', False)
                    
                    if is_simulated:
                        logger.warning("Usando dados simulados devido a falha na API real")
                    
                    if flights:
                        logger.info(f"Encontrados {len(flights)} voos. Preços: {[f['price'] for f in flights[:3]]}")
                        additional_context += f"\n\nEncontrei {len(flights)} voos para {travel_info['destination']} saindo de {travel_info['origin']} em {travel_info['departure_date']}.\n"
                        
                        if is_simulated:
                            additional_context += "\n(NOTA: Estes são dados aproximados baseados em tendências de mercado, não preços em tempo real.)\n"

                        # Adicionar detalhes dos 3 melhores voos
                        top_flights = flights[:3]
                        for i, flight in enumerate(top_flights):
                            price = flight.get('price', 'N/A')
                            currency = flight.get('currency', 'BRL')
                            airline = flight.get('airline', 'Companhia não informada')
                            departure_time = flight.get('departure', {}).get('time', 'N/A')
                            arrival_time = flight.get('arrival', {}).get('time', 'N/A')

                            # Formatar as datas
                            try:
                                dep_time = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
                                arr_time = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
                                departure_time = dep_time.strftime("%d/%m/%Y %H:%M")
                                arrival_time = arr_time.strftime("%d/%m/%Y %H:%M")
                            except Exception as e:
                                logger.warning(f"Erro ao formatar datas: {str(e)}")

                            additional_context += f"\nOpção {i+1}: {airline} - {departure_time} a {arrival_time} - {price} {currency}"

                            # Adicionar o link de afiliado
                            additional_context += f"\nLink para compra: [[LINK_COMPRA:{flight.get('affiliate_link', '')}]]"
                else:
                    logger.error(f"Erro na busca de voos: {flight_data.get('error', 'Erro desconhecido')}")

            # Buscar melhores preços se a data é flexível
            if travel_info.get('is_flexible') and travel_info.get('date_range_start') and travel_info.get('date_range_end'):
                logger.info(f"Buscando melhores preços para o período: {travel_info['date_range_start']} a {travel_info['date_range_end']}")
                best_prices_data = search_best_prices(travel_info)
                logger.info(f"Resultados da busca de melhores preços: {best_prices_data.keys() if isinstance(best_prices_data, dict) else 'Nenhum'}")

                if 'error' not in best_prices_data:
                    best_prices = best_prices_data.get('best_prices', [])
                    is_simulated = best_prices_data.get('is_simulated', False)
                    
                    if is_simulated:
                        logger.warning("Usando dados simulados devido a falha na API real")
                    
                    if best_prices:
                        logger.info(f"Encontradas {len(best_prices)} ofertas. Preços: {[p['price'] for p in best_prices[:3]]}")
                        additional_context += f"\n\nEncontrei as melhores ofertas para {travel_info['destination']} saindo de {travel_info['origin']} no período solicitado.\n"
                        
                        if is_simulated:
                            additional_context += "\n(NOTA: Estes são dados aproximados baseados em tendências de mercado, não preços em tempo real.)\n"

                        # Adicionar as 3 melhores ofertas
                        top_prices = best_prices[:3]
                        for i, price_info in enumerate(top_prices):
                            date = price_info.get('date', 'N/A')
                            price = price_info.get('price', 'N/A')
                            currency = price_info.get('currency', 'BRL')

                            # Formatar a data
                            try:
                                flight_date = datetime.fromisoformat(date)
                                date = flight_date.strftime("%d/%m/%Y")
                            except Exception as e:
                                logger.warning(f"Erro ao formatar data: {str(e)}")

                            additional_context += f"\nOferta {i+1}: {date} - {price} {currency}"

                            # Adicionar o link de afiliado
                            additional_context += f"\nLink para compra: [[LINK_COMPRA:{price_info.get('affiliate_link', '')}]]"
                else:
                    logger.error(f"Erro na busca de melhores preços: {best_prices_data.get('error', 'Erro desconhecido')}")

        # Chamar o assistente da OpenAI com o contexto adicional
        updated_context = system_context
        if additional_context:
            logger.info("Adicionando contexto de resultados de busca ao prompt do OpenAI")
            updated_context += additional_context
        else:
            logger.info("Nenhum resultado de busca para adicionar ao contexto")

        result = openai_service.travel_assistant(
            user_message=message,
            conversation_history=history,
            system_context=updated_context
        )

        # Verificar se houve erro na chamada à API
        if 'error' in result:
            logger.error(f"Erro ao chamar a API OpenAI: {result['error']}")
            return {"error": True, "message": "Erro ao processar sua mensagem. Por favor, tente novamente em alguns instantes."}

        # Extrair a resposta principal
        assistant_response = result.get('response', '')

        # Verificar se a resposta contém um link de compra
        purchase_link = None
        if '[[LINK_COMPRA:' in assistant_response:
            link_match = re.search(r'\[\[LINK_COMPRA:(.*?)\]\]', assistant_response)
            if link_match:
                purchase_link = link_match.group(1).strip()
                # Remover o marcador do texto
                assistant_response = assistant_response.replace(link_match.group(0), '')

        # Montar resposta final
        response = {
            "response": assistant_response.strip()
        }

        # Adicionar link de compra se encontrado
        if purchase_link:
            response["purchase_link"] = purchase_link

        # Adicionar dados de voos se disponíveis
        if flight_data and 'error' not in flight_data:
            response["flight_data"] = flight_data

        # Adicionar dados de melhores preços se disponíveis
        if best_prices_data and 'error' not in best_prices_data:
            response["best_prices_data"] = best_prices_data

        return response

    except Exception as e:
        logger.exception(f"Erro ao processar mensagem no modo busca rápida: {str(e)}")
        return {"error": True, "message": f"Ocorreu um erro inesperado: {str(e)}"}

def extract_travel_info(message, history):
    """
    Extrai informações de viagem da mensagem e histórico usando NLP
    """
    # Inicializar estrutura de dados
    travel_info = {
        'origin': None,
        'destination': None,
        'departure_date': None,
        'return_date': None,
        'is_flexible': False,
        'date_range_start': None,
        'date_range_end': None,
        'adults': 1
    }

    # Combinar mensagem atual com histórico para análise completa
    full_text = message
    for item in history:
        if isinstance(item, dict):
            if 'user' in item:
                full_text += " " + item['user']
            if 'assistant' in item:
                full_text += " " + item['assistant']

    # Detectar origem e destino com regex simples
    # Padrões comuns de origem/destino em português
    origin_patterns = [
        r'(?:sa(?:i|í)(?:r|ndo) de|partindo de|origem) ([A-Za-z\s]+)',
        r'(?:de|da|do) ([A-Za-z\s]+) (?:para|a|ao|até)',
        r'voo (?:de|da|do) ([A-Za-z\s]+)'
    ]

    destination_patterns = [
        r'(?:para|a|ao|até) ([A-Za-z\s]+)',
        r'(?:destino|chegando (?:a|em)|ir para) ([A-Za-z\s]+)',
        r'voo (?:para|a) ([A-Za-z\s]+)'
    ]

    # Detectar datas com regex
    date_patterns = [
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # DD/MM/YYYY ou DD-MM-YYYY
        r'(\d{1,2} de [a-zA-Zç]+ de \d{2,4})'  # DD de Month de YYYY
    ]

    month_patterns = [
        r'(?:em|no mês de|durante|para) (janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)',
        r'(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[\.eiro]*'
    ]

    # Aplicar padrões de origem
    for pattern in origin_patterns:
        matches = re.search(pattern, full_text, re.IGNORECASE)
        if matches:
            travel_info['origin'] = matches.group(1).strip()
            break

    # Aplicar padrões de destino
    for pattern in destination_patterns:
        matches = re.search(pattern, full_text, re.IGNORECASE)
        if matches:
            # Evitar que a origem seja detectada como destino
            dest = matches.group(1).strip()
            if dest != travel_info['origin']:
                travel_info['destination'] = dest
                break

    # Detectar flexibilidade de datas
    if re.search(r'(?:flex(?:ível|ibilidade)|qualquer data|melhor(?:es)? data)', full_text, re.IGNORECASE):
        travel_info['is_flexible'] = True

    # Detectar datas específicas
    dates_found = []
    for pattern in date_patterns:
        matches = re.finditer(pattern, full_text, re.IGNORECASE)
        for match in matches:
            dates_found.append(match.group(1))

    # Processar datas encontradas
    if len(dates_found) >= 1:
        travel_info['departure_date'] = normalize_date(dates_found[0])

        if len(dates_found) >= 2:
            travel_info['return_date'] = normalize_date(dates_found[1])

    # Detectar meses para períodos flexíveis
    months_found = []
    for pattern in month_patterns:
        matches = re.finditer(pattern, full_text, re.IGNORECASE)
        for match in matches:
            months_found.append(match.group(1).lower())

    # Processar meses para períodos flexíveis
    if months_found:
        travel_info['is_flexible'] = True

        # Mapear nomes de meses para números
        month_map = {
            'janeiro': 1, 'jan': 1,
            'fevereiro': 2, 'fev': 2,
            'março': 3, 'mar': 3,
            'abril': 4, 'abr': 4,
            'maio': 5, 'mai': 5,
            'junho': 6, 'jun': 6,
            'julho': 7, 'jul': 7,
            'agosto': 8, 'ago': 8,
            'setembro': 9, 'set': 9,
            'outubro': 10, 'out': 10,
            'novembro': 11, 'nov': 11,
            'dezembro': 12, 'dez': 12
        }

        # Obter o número do mês
        for month_name in months_found:
            for key, month_num in month_map.items():
                if month_name.startswith(key):
                    # Definir período de um mês
                    current_year = datetime.now().year
                    start_date = datetime(current_year, month_num, 1)

                    # Se o mês já passou este ano, usar o próximo ano
                    if start_date < datetime.now():
                        start_date = datetime(current_year + 1, month_num, 1)

                    # Definir o último dia do mês
                    if month_num == 12:
                        end_date = datetime(current_year + 1, 1, 1) - timedelta(days=1)
                    else:
                        end_date = datetime(current_year, month_num + 1, 1) - timedelta(days=1)

                    travel_info['date_range_start'] = start_date.strftime('%Y-%m-%d')
                    travel_info['date_range_end'] = end_date.strftime('%Y-%m-%d')
                    break

    # Converter nomes de cidades em códigos IATA, se necessário
    if travel_info['origin']:
        travel_info['origin'] = get_iata_code(travel_info['origin'])

    if travel_info['destination']:
        travel_info['destination'] = get_iata_code(travel_info['destination'])

    return travel_info

def normalize_date(date_str):
    """
    Normaliza uma string de data para o formato YYYY-MM-DD
    """
    try:
        # Tentar diferentes formatos
        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d',
            '%d/%m/%y', '%d-%m-%y',
            '%d de %B de %Y', '%d %B %Y'
        ]

        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # Se nenhum formato funcionar, tentar mais manualmente
        parts = re.split(r'[/\-]', date_str)
        if len(parts) == 3:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])

            # Ajustar ano se for abreviado
            if year < 100:
                year += 2000 if year < 50 else 1900

            return f"{year:04d}-{month:02d}-{day:02d}"

    except Exception:
        pass

    return date_str

def get_iata_code(city_name):
    """
    Converte um nome de cidade em código IATA
    Em uma implementação real, isso usaria uma API ou banco de dados
    Para simplicidade, implementamos apenas os códigos mais comuns
    """
    city_to_iata = {
        'são paulo': 'GRU',
        'sao paulo': 'GRU',
        'rio de janeiro': 'RIO',
        'rio': 'RIO',
        'brasília': 'BSB',
        'brasilia': 'BSB',
        'salvador': 'SSA',
        'recife': 'REC',
        'fortaleza': 'FOR',
        'belo horizonte': 'CNF',
        'curitiba': 'CWB',
        'porto alegre': 'POA',
        'belém': 'BEL',
        'belem': 'BEL',
        'manaus': 'MAO',
        'goiânia': 'GYN',
        'goiania': 'GYN',

        'nova york': 'NYC',
        'new york': 'NYC',
        'miami': 'MIA',
        'orlando': 'MCO',
        'los angeles': 'LAX',
        'chicago': 'ORD',
        'las vegas': 'LAS',
        'toronto': 'YYZ',
        'cidade do méxico': 'MEX',
        'cidade do mexico': 'MEX',
        'mexico': 'MEX',
        'cancún': 'CUN',
        'cancun': 'CUN',

        'londres': 'LON',
        'london': 'LON',
        'paris': 'PAR',
        'roma': 'ROM',
        'madrid': 'MAD',
        'barcelona': 'BCN',
        'amsterdam': 'AMS',
        'berlim': 'BER',
        'frankfurt': 'FRA',
        'munique': 'MUC',
        'lisboa': 'LIS',
        'porto': 'OPO',

        'tóquio': 'TYO',
        'tokio': 'TYO',
        'tokyo': 'TYO',
        'pequim': 'BJS',
        'beijing': 'BJS',
        'xangai': 'SHA',
        'shanghai': 'SHA',
        'hong kong': 'HKG',
        'seul': 'SEL',
        'seoul': 'SEL',
        'bangkok': 'BKK',
        'singapura': 'SIN',
        'singapore': 'SIN',
        'dubai': 'DXB',
        'sidney': 'SYD',
        'sydney': 'SYD',
        'melbourne': 'MEL',
        'auckland': 'AKL',
    }

    # Normalizar o nome da cidade (minúsculas e sem acentos)
    import unicodedata
    def normalize_text(text):
        return unicodedata.normalize('NFKD', text.lower()).encode('ASCII', 'ignore').decode('ASCII')

    normalized_city = normalize_text(city_name)

    # Buscar correspondência exata
    if normalized_city in city_to_iata:
        return city_to_iata[normalized_city]

    # Buscar correspondência parcial
    for city, code in city_to_iata.items():
        if normalized_city in city or city in normalized_city:
            return code

    # Se não encontrar, retornar o nome original
    return city_name

def is_ready_for_search(travel_info):
    """
    Verifica se temos informações suficientes para fazer uma busca
    """
    # Verificar se temos pelo menos origem e destino
    if not travel_info.get('origin') or not travel_info.get('destination'):
        return False

    # Verificar se temos data de partida ou um período flexível
    has_departure = travel_info.get('departure_date') is not None
    has_range = travel_info.get('is_flexible') and travel_info.get('date_range_start') and travel_info.get('date_range_end')

    return has_departure or has_range

def search_flights(travel_info):
    """
    Busca voos através do serviço Skyscanner com fallback para Amadeus
    """
    try:
        # Preparar parâmetros para a API
        params = {
            'origin': travel_info.get('origin'),
            'destination': travel_info.get('destination'),
            'departure_date': travel_info.get('departure_date'),
            'return_date': travel_info.get('return_date'),
            'adults': travel_info.get('adults', 1),
            'currency': 'BRL'
        }

        logger.info(f"Iniciando busca de voos com parâmetros: {params}")
        
        # Inicializar o serviço Amadeus - já preparado para uso imediato
        from services.amadeus_service import AmadeusService
        amadeus_service = AmadeusService()
        
        # Tentar primeiro o Skyscanner
        logger.info("Tentando buscar voos via Skyscanner")
        skyscanner_flights = skyscanner_service.search_flights(params)
        
        # Verificar se a busca do Skyscanner foi bem-sucedida
        skyscanner_success = 'error' not in skyscanner_flights and skyscanner_flights.get('flights', [])
        
        # Se não tiver resultados do Skyscanner, usar o Amadeus diretamente
        if not skyscanner_success:
            logger.warning(f"Sem resultados do Skyscanner ou erro encontrado: {skyscanner_flights.get('error', 'Sem voos encontrados')}")
            logger.info("Buscando voos via Amadeus")
            
            # Mapear parâmetros para o formato da Amadeus
            amadeus_params = {
                'originLocationCode': params['origin'],
                'destinationLocationCode': params['destination'],
                'departureDate': params['departure_date'],
                'adults': params['adults'],
                'currencyCode': params['currency']
            }
            
            if params.get('return_date'):
                amadeus_params['returnDate'] = params['return_date']
            
            # Buscar voos na Amadeus
            amadeus_flights = amadeus_service.search_flights(amadeus_params)
            
            if 'error' not in amadeus_flights:
                # Processar os resultados do Amadeus
                flights = []
                
                # Obter dados dos voos
                for flight in amadeus_flights.get('data', []):
                    try:
                        # Extrair informações básicas
                        flight_id = flight.get('id', '')
                        price_info = flight.get('price', {})
                        price = price_info.get('total', '0')
                        currency = price_info.get('currency', 'BRL')
                        
                        # Extrair informações de itinerário
                        itineraries = flight.get('itineraries', [])
                        if not itineraries:
                            continue
                            
                        itinerary = itineraries[0]
                        segments = itinerary.get('segments', [])
                        
                        if not segments:
                            continue
                            
                        # Detalhes da partida
                        first_segment = segments[0]
                        departure_info = first_segment.get('departure', {})
                        origin_code = departure_info.get('iataCode', params.get('origin'))
                        departure_at = departure_info.get('at', '')
                        
                        # Detalhes da chegada
                        last_segment = segments[-1]
                        arrival_info = last_segment.get('arrival', {})
                        destination_code = arrival_info.get('iataCode', params.get('destination'))
                        arrival_at = arrival_info.get('at', '')
                        
                        # Companhia aérea
                        carrier_code = first_segment.get('carrierCode', '')
                        
                        # Mapear códigos de companhias para nomes (simplificado)
                        airline_map = {
                            'LA': 'LATAM',
                            'G3': 'GOL',
                            'AD': 'Azul',
                            'EK': 'Emirates',
                            'AF': 'Air France',
                            'BA': 'British Airways',
                            'AA': 'American Airlines',
                            'UA': 'United Airlines',
                            'DL': 'Delta Airlines',
                            'IB': 'Iberia',
                            'LH': 'Lufthansa',
                        }
                        
                        airline = airline_map.get(carrier_code, carrier_code)
                        
                        # Gerar links específicos das companhias aéreas
                        airline_links = {
                            'LATAM': f"https://www.latamairlines.com/br/pt/ofertas-voos?origin={origin_code}&destination={destination_code}&outbound={departure_at.split('T')[0]}&inbound={params.get('return_date', '')}&adt=1&chd=0&inf=0",
                            'GOL': f"https://www.voegol.com.br/pt/selecao-voos?origin={origin_code}&destination={destination_code}&departure={departure_at.split('T')[0]}&return={params.get('return_date', '')}&adults=1&children=0&infants=0",
                            'Azul': f"https://www.voeazul.com.br/br/en/home?s_cid=sem:latam:google:G_Brand_Brasil_Termos_Curtos:azul",
                            'Emirates': f"https://www.emirates.com/br/portuguese/",
                            'Air France': f"https://wwws.airfrance.fr/",
                            'British Airways': f"https://www.britishairways.com/travel/home/public/en_br",
                            'American Airlines': f"https://www.aa.com/homePage.do?locale=pt_BR",
                            'Delta Airlines': f"https://www.delta.com/",
                            'Iberia': f"https://www.iberia.com/br/",
                            'Lufthansa': f"https://www.lufthansa.com/br/pt/homepage",
                        }
                        
                        # Definir o link de compra preferencial (primeiro da companhia aérea, depois o Skyscanner como fallback)
                        airline_link = airline_links.get(airline)
                        skyscanner_link = skyscanner_service._generate_affiliate_link(
                            origin_code, 
                            destination_code, 
                            departure_at.split('T')[0] if 'T' in departure_at else '',
                            params.get('return_date')
                        )
                        
                        # Preferir link da companhia aérea se disponível
                        purchase_link = airline_link if airline_link else skyscanner_link
                        
                        # Formar o objeto de voo
                        formatted_flight = {
                            "id": flight_id,
                            "price": float(price),
                            "currency": currency,
                            "departure": {
                                "airport": origin_code,
                                "time": departure_at
                            },
                            "arrival": {
                                "airport": destination_code,
                                "time": arrival_at
                            },
                            "duration": itinerary.get('duration', ''),
                            "segments": len(segments),
                            "airline": airline,
                            "affiliate_link": purchase_link,
                            "direct_airline_link": airline_link,
                            "skyscanner_link": skyscanner_link,
                            "source": "amadeus"
                        }
                        
                        flights.append(formatted_flight)
                        
                    except Exception as segment_e:
                        logger.error(f"Erro ao processar segmento de voo Amadeus: {str(segment_e)}")
                
                # Ordenar por preço
                flights.sort(key=lambda x: x["price"])
                
                logger.info(f"Encontrados {len(flights)} voos via Amadeus")
                return {"flights": flights, "source": "amadeus"}
            else:
                logger.error(f"Erro ao buscar voos na Amadeus: {amadeus_flights.get('error', 'Erro desconhecido')}")
                
                # Se dados simulados estiverem disponíveis, usar como último recurso
                try:
                    logger.info("Usando dados simulados como último recurso")
                    flights = amadeus_service._get_mock_flights(amadeus_params).get('data', [])
                    processed_flights = []
                    
                    # Processar dados simulados para o formato padrão
                    for flight in flights:
                        try:
                            itineraries = flight.get('itineraries', [])
                            if not itineraries:
                                continue
                                
                            segments = itineraries[0].get('segments', [])
                            if not segments:
                                continue
                                
                            first_segment = segments[0]
                            departure_info = first_segment.get('departure', {})
                            arrival_info = segments[-1].get('arrival', {})
                            
                            price_info = flight.get('price', {})
                            price = price_info.get('total', '0')
                            
                            processed_flight = {
                                "id": flight.get('id', ''),
                                "price": float(price),
                                "currency": "BRL",
                                "departure": {
                                    "airport": departure_info.get('iataCode', params.get('origin')),
                                    "time": departure_info.get('at', '')
                                },
                                "arrival": {
                                    "airport": arrival_info.get('iataCode', params.get('destination')),
                                    "time": arrival_info.get('at', '')
                                },
                                "airline": "Companhia Simulada",
                                "affiliate_link": f"https://www.skyscanner.com.br/transport/flights/{params.get('origin')}/{params.get('destination')}/?adults=1&adultsv2=1",
                                "source": "simulado"
                            }
                            
                            processed_flights.append(processed_flight)
                            
                        except Exception as sim_e:
                            logger.error(f"Erro ao processar voo simulado: {str(sim_e)}")
                            
                    if processed_flights:
                        logger.info(f"Usando {len(processed_flights)} voos simulados como último recurso")
                        return {"flights": processed_flights, "source": "simulado", "is_simulated": True}
                    
                except Exception as mock_e:
                    logger.error(f"Erro ao usar dados simulados: {str(mock_e)}")
                    
        # Se a busca do Skyscanner foi bem-sucedida, adicionar links diretos das companhias aéreas
        if skyscanner_success:
            flights = skyscanner_flights.get('flights', [])
            for flight in flights:
                airline = flight.get('airline', '')
                origin = params.get('origin', '')
                destination = params.get('destination', '')
                departure_date = params.get('departure_date', '')
                return_date = params.get('return_date', '')
                
                # Gerar links específicos das companhias aéreas
                airline_links = {
                    'LATAM': f"https://www.latamairlines.com/br/pt/ofertas-voos?origin={origin}&destination={destination}&outbound={departure_date}&inbound={return_date}&adt=1&chd=0&inf=0",
                    'GOL': f"https://www.voegol.com.br/pt/selecao-voos?origin={origin}&destination={destination}&departure={departure_date}&return={return_date}&adults=1&children=0&infants=0",
                    'Azul': f"https://www.voeazul.com.br/br/en/home?s_cid=sem:latam:google:G_Brand_Brasil_Termos_Curtos:azul",
                    # Adicionar mais companhias conforme necessário
                }
                
                # Adicionar link direto da companhia aérea se disponível
                flight['direct_airline_link'] = airline_links.get(airline)
                flight['source'] = "skyscanner"
            
            logger.info(f"Encontrados {len(flights)} voos via Skyscanner")
            return skyscanner_flights
            
        # Se chegou aqui, nenhuma API funcionou
        return {"error": "Não foi possível encontrar voos disponíveis. Por favor, tente outra data ou destino.", "is_simulated": True}

    except Exception as e:
        logger.error(f"Erro ao buscar voos: {str(e)}")
        return {"error": f"Erro ao buscar voos: {str(e)}"}

def search_best_prices(travel_info):
    """
    Busca melhores preços para um período flexível
    """
    try:
        logger.info(f"Buscando melhores preços para {travel_info.get('origin')} -> {travel_info.get('destination')}")
        
        # Tentar primeiro o Skyscanner
        result = skyscanner_service.get_best_price_options(
            origin=travel_info.get('origin'),
            destination=travel_info.get('destination'),
            date_range_start=travel_info.get('date_range_start'),
            date_range_end=travel_info.get('date_range_end')
        )
        
        if 'error' in result:
            logger.warning(f"Erro ao buscar preços no Skyscanner: {result['error']}")
            
            # Tentar usar a API da Amadeus como fallback
            try:
                logger.info("Tentando API da Amadeus como fallback para preços")
                # Implementar chamada à API da Amadeus aqui se necessário
            except Exception as amadeus_e:
                logger.error(f"Erro ao usar API da Amadeus para preços: {str(amadeus_e)}")
                
        return result

    except Exception as e:
        logger.error(f"Erro ao buscar melhores preços: {str(e)}")
        return {"error": f"Erro ao buscar melhores preços: {str(e)}"}

def process_message(user_message, conversation_history=None):
    """
    Processa a mensagem do usuário e retorna uma resposta adequada
    utilizando o fluxo de busca rápida de passagens
    """
    if conversation_history is None:
        conversation_history = []
    
    try:
        # Analisar a mensagem do usuário usando o GPT para extrair informações de viagem
        system_context = BUSCA_RAPIDA_PROMPT
        
        # Preparar mensagem para o GPT
        prompt_messages = [
            {"role": "system", "content": system_context},
            {"role": "user", "content": user_message}
        ]
        
        # Adicionar histórico da conversa, se existir
        for msg in conversation_history:
            if msg.get('is_user'):
                prompt_messages.append({"role": "user", "content": msg.get('content', '')})
            else:
                prompt_messages.append({"role": "assistant", "content": msg.get('content', '')})
        
        # Chamar o OpenAI para analisar a mensagem
        logger.info("Enviando mensagem para análise pelo OpenAI")
        response = openai_service.create_chat_completion(prompt_messages)
        
        if 'error' in response:
            logger.error(f"Erro na chamada à API OpenAI: {response['error']}")
            return {"response": f"Desculpe, estou tendo problemas para processar sua solicitação. Por favor, tente novamente em alguns instantes."}
        
        # Extrair a resposta do GPT
        gpt_response = response['choices'][0]['message']['content']
        
        # Verificar se a resposta contém o marcador JSON com informações de viagem
        travel_info_match = re.search(r'```json\s*\n(.*?)\n\s*```', gpt_response, re.DOTALL)
        
        if travel_info_match:
            # Extrair e processar as informações da viagem
            travel_info_json = travel_info_match.group(1)
            try:
                travel_info = json.loads(travel_info_json)
                logger.info(f"Informações de viagem extraídas: {travel_info}")
                
                # Verificar se temos informações suficientes para buscar voos
                if is_flight_search_ready(travel_info):
                    # Buscar voos conforme as informações extraídas
                    if has_flexible_dates(travel_info):
                        logger.info("Buscando melhores preços para datas flexíveis")
                        search_results = search_best_prices(travel_info)
                    else:
                        logger.info("Buscando voos para datas específicas")
                        search_results = search_flights(travel_info)
                    
                    # Processar os resultados com o GPT para formatar uma resposta amigável
                    if 'error' not in search_results:
                        prompt_with_results = [
                            {"role": "system", "content": system_context},
                            {"role": "user", "content": user_message},
                            {"role": "assistant", "content": gpt_response},
                            {"role": "user", "content": f"Aqui estão os resultados da busca: ```json\n{json.dumps(search_results, ensure_ascii=False)}\n```\nPor favor, formate esses resultados de maneira amigável e apresente as melhores opções para o usuário, incluindo os links para compra quando disponíveis. Se houver links de afiliados, use o formato [[LINK_COMPRA:URL]] para exibi-los."}
                        ]
                        
                        final_response = openai_service.create_chat_completion(prompt_with_results)
                        if 'error' not in final_response:
                            return {"response": final_response['choices'][0]['message']['content']}
                    
                    # Se houve erro na busca ou no processamento final
                    if 'error' in search_results:
                        logger.error(f"Erro na busca: {search_results['error']}")
                        return {"response": f"Desculpe, encontrei um problema ao buscar as passagens: {search_results['error']}. Poderia fornecer mais detalhes sobre sua viagem para que eu possa tentar novamente?"}
                
                # Se não tivermos informações suficientes, retornar a resposta original do GPT
                return {"response": gpt_response}
                
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON das informações de viagem: {travel_info_json}")
                return {"response": gpt_response}
        else:
            # Se não tiver marcador JSON, é uma resposta normal do GPT
            return {"response": gpt_response}
            
    except Exception as e:
        logger.error(f"Erro no processamento da mensagem: {str(e)}")
        return {"response": "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde."}