
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
        
        # Se temos informações suficientes para fazer uma busca, adicionar ao contexto
        additional_context = ""
        flight_data = None
        best_prices_data = None
        
        if is_ready_for_search(travel_info):
            # Buscar voos específicos se temos datas específicas
            if travel_info.get('departure_date') and not travel_info.get('is_flexible'):
                flight_data = search_flights(travel_info)
                
                if 'error' not in flight_data:
                    flights = flight_data.get('flights', [])
                    if flights:
                        additional_context += f"\n\nEncontrei {len(flights)} voos para {travel_info['destination']} saindo de {travel_info['origin']} em {travel_info['departure_date']}.\n"
                        
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
                            except:
                                pass
                            
                            additional_context += f"\nOpção {i+1}: {airline} - {departure_time} a {arrival_time} - {price} {currency}"
                            
                            # Adicionar o link de afiliado
                            additional_context += f"\nLink para compra: [[LINK_COMPRA:{flight.get('affiliate_link', '')}]]"
            
            # Buscar melhores preços se a data é flexível
            if travel_info.get('is_flexible') and travel_info.get('date_range_start') and travel_info.get('date_range_end'):
                best_prices_data = search_best_prices(travel_info)
                
                if 'error' not in best_prices_data:
                    best_prices = best_prices_data.get('best_prices', [])
                    if best_prices:
                        additional_context += f"\n\nEncontrei as melhores ofertas para {travel_info['destination']} saindo de {travel_info['origin']} no período solicitado.\n"
                        
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
                            except:
                                pass
                            
                            additional_context += f"\nOferta {i+1}: {date} - {price} {currency}"
                            
                            # Adicionar o link de afiliado
                            additional_context += f"\nLink para compra: [[LINK_COMPRA:{price_info.get('affiliate_link', '')}]]"
        
        # Chamar o assistente da OpenAI com o contexto adicional
        updated_context = system_context
        if additional_context:
            updated_context += additional_context
            
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
    Busca voos através do serviço Skyscanner
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
        
        # Chamar o serviço Skyscanner
        return skyscanner_service.search_flights(params)
    
    except Exception as e:
        logger.error(f"Erro ao buscar voos: {str(e)}")
        return {"error": f"Erro ao buscar voos: {str(e)}"}

def search_best_prices(travel_info):
    """
    Busca melhores preços para um período flexível
    """
    try:
        return skyscanner_service.get_best_price_options(
            origin=travel_info.get('origin'),
            destination=travel_info.get('destination'),
            date_range_start=travel_info.get('date_range_start'),
            date_range_end=travel_info.get('date_range_end')
        )
    
    except Exception as e:
        logger.error(f"Erro ao buscar melhores preços: {str(e)}")
        return {"error": f"Erro ao buscar melhores preços: {str(e)}"}
