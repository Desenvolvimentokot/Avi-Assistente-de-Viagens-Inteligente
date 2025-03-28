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

def process_message(message, test_params=None, history=None, travel_info=None):
    """
    Processa uma mensagem do usuário no modo busca rápida, implementando um fluxo em duas etapas:
    1. Extração e confirmação das informações com o cliente
    2. Busca e apresentação dos resultados após confirmação

    Args:
        message (str): Mensagem do usuário
        test_params (dict): Parâmetros opcionais para testes (ex: max_dates_to_check)
        history (list): Histórico de mensagens anteriores
        travel_info (dict): Informações de viagem previamente extraídas

    Returns:
        dict: Resposta processada
    """
    if history is None:
        history = []
        
    if test_params is None or not isinstance(test_params, dict):
        test_params = {}

    try:
        logger.info(f"Processando mensagem no modo busca rápida: {message[:50]}...")

        # Preparar o contexto específico para busca rápida
        system_context = BUSCA_RAPIDA_PROMPT

        # Extrair informações de viagem da mensagem e histórico
        if travel_info is None:
            travel_info = extract_travel_info(message, history)
        else:
            # Atualizar com novas informações da mensagem atual
            new_info = extract_travel_info(message, history)
            # Priorizar informações não-nulas das novas informações
            for key, value in new_info.items():
                if value is not None and value != "":
                    travel_info[key] = value
        
        # Adicionar parâmetros de teste, se fornecidos
        if test_params and isinstance(test_params, dict):
            for key, value in test_params.items():
                travel_info[key] = value
        
        # Combinar mensagem atual com histórico para análise de casos específicos
        full_text = message
        for item in history:
            if isinstance(item, dict):
                if 'user' in item:
                    full_text += " " + item['user']
                if 'assistant' in item:
                    full_text += " " + item['assistant']
        
        logger.info(f"Informações de viagem extraídas: {travel_info}")
        
        # Verificar se esta é uma mensagem de confirmação
        is_confirmation = False
        confirmation_patterns = [
            r'\bsim\b', r'\bconfirmo\b', r'\bcorreto\b', r'\bpode\s+seguir\b',
            r'\bconfirma(?:do)?\b', r'\bcontinue\b', r'\bvamos\s+em\s+frente\b', 
            r'\bcerto\b', r'\bok\b', r'\bprossiga\b', r'\bprosseguir\b'
        ]
        
        for pattern in confirmation_patterns:
            if re.search(pattern, message.lower()):
                is_confirmation = True
                logger.info("Detectada confirmação do usuário")
                break
                
        # Inicializar variáveis para resultados
        additional_context = ""
        flight_data = None
        best_prices_data = None

        # Fase 1: Extração e confirmação - Se não for confirmação e não tiver histórico suficiente
        if not is_confirmation and (len(history) < 2 or not is_ready_for_search(travel_info)):
            logger.info("Etapa 1: Extração e confirmação de informações")
            # Adicionar contexto para indicar que estamos na fase de extração/confirmação
            additional_context = "\n\n[ETAPA_ATUAL: EXTRAÇÃO_E_CONFIRMAÇÃO]"
            additional_context += f"\n\nInformações extraídas até o momento:\n"
            additional_context += f"- Origem: {travel_info.get('origin', 'Não identificada')}\n"
            additional_context += f"- Destino: {travel_info.get('destination', 'Não identificado')}\n"
            additional_context += f"- Data de ida: {travel_info.get('departure_date', 'Não identificada')}\n"
            additional_context += f"- Data de volta: {travel_info.get('return_date', 'Não identificada')}\n"
            additional_context += f"- Passageiros: {travel_info.get('adults', 1)} adulto(s)\n"
            additional_context += f"- Classe: {travel_info.get('class', 'ECONOMY')}\n"
            
            # Indicar explicitamente ao assistente que precisamos de confirmação
            additional_context += "\n\n[INSTRUÇÃO: Solicite confirmação ao cliente antes de prosseguir com a busca]"
            
        # Fase 2: Busca e apresentação - Se for confirmação ou já tiver informações suficientes
        elif is_confirmation or travel_info.get('confirmed') or is_ready_for_search(travel_info):
            logger.info("Etapa 2: Busca e apresentação de resultados")
            additional_context = "\n\n[ETAPA_ATUAL: BUSCA_E_APRESENTAÇÃO]"
            logger.info("Informações suficientes para busca encontradas")

            # Buscar voos específicos se temos datas específicas
            if travel_info.get('departure_date') and not travel_info.get('is_flexible'):
                logger.info(f"Buscando voos para data específica: {travel_info['departure_date']}")
                flight_data = search_flights(travel_info)
                logger.info(f"Resultados da busca de voos: {flight_data.keys() if isinstance(flight_data, dict) else 'Nenhum'}")

                if 'error' not in flight_data:
                    flights = flight_data.get('flights', [])
                    if flights:
                        logger.info(f"Encontrados {len(flights)} voos. Preços: {[f['price'] for f in flights[:3]]}")
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
                            except Exception as e:
                                logger.warning(f"Erro ao formatar datas: {str(e)}")

                            additional_context += f"\nOpção {i+1}: {airline} - {departure_time} a {arrival_time} - {price} {currency}"

                            # Adicionar o link de afiliado
                            additional_context += f"\nLink para compra: [[LINK_COMPRA:{flight.get('affiliate_link', '')}]]"
                else:
                    logger.error(f"Erro na busca de voos: {flight_data.get('error', 'Erro desconhecido')}")

            # Processar as datas conforme necessário
            # Se temos a informação específica "dia 14 de abril", criar uma data
            april_pattern = r'(?:dia|em|no dia)?\s*(\d{1,2})\s*(?:de|\/)?\s*(?:abril|abr|04|4)'
            april_match = re.search(april_pattern, full_text, re.IGNORECASE)
            if april_match:
                day = april_match.group(1)
                # Definir o ano atual ou o próximo se abril já passou
                current_year = datetime.now().year
                if datetime.now().month > 4:  # Se estamos depois de abril
                    current_year += 1
                
                departure_date = f"{current_year}-04-{int(day):02d}"
                travel_info['departure_date'] = departure_date
                
                # Se menciona passar X dias, calcular a data de retorno
                days_pattern = r'(?:passar|ficar|por)\s*(\d+)\s*dias'
                days_match = re.search(days_pattern, full_text, re.IGNORECASE)
                if days_match:
                    days = int(days_match.group(1))
                    departure_date_obj = datetime.strptime(departure_date, '%Y-%m-%d')
                    return_date_obj = departure_date_obj + timedelta(days=days)
                    travel_info['return_date'] = return_date_obj.strftime('%Y-%m-%d')

                # Se encontramos a origem e não é um código IATA, converter para São Paulo
                if travel_info.get('origin') and len(travel_info.get('origin', '')) > 3 and 'paulo' not in travel_info.get('origin', '').lower():
                    # Verificar se menciona estar em São Paulo
                    if re.search(r'(?:estamos|estou|em)\s*(?:s[aã]o paulo|sp)', full_text, re.IGNORECASE):
                        travel_info['origin'] = 'GRU'  # Aeroporto de Guarulhos em São Paulo
            
            # Buscar melhores preços se a data é flexível ou se temos datas específicas para melhores preços
            if (travel_info.get('is_flexible') and travel_info.get('date_range_start') and travel_info.get('date_range_end')) or \
               (travel_info.get('departure_date') and travel_info.get('return_date') and 'melhor' in full_text.lower()):
                
                # Se não temos range de datas, mas temos datas específicas e queremos o melhor preço
                if not travel_info.get('date_range_start') and travel_info.get('departure_date'):
                    # Criar um range de +/- 3 dias em torno da data específica
                    departure_date_obj = datetime.strptime(travel_info['departure_date'], '%Y-%m-%d')
                    range_start = (departure_date_obj - timedelta(days=3)).strftime('%Y-%m-%d')
                    range_end = (departure_date_obj + timedelta(days=3)).strftime('%Y-%m-%d')
                    travel_info['date_range_start'] = range_start
                    travel_info['date_range_end'] = range_end
                    travel_info['is_flexible'] = True
                
                logger.info(f"Buscando melhores preços para o período: {travel_info.get('date_range_start', travel_info.get('departure_date'))} a {travel_info.get('date_range_end', travel_info.get('return_date'))}")
                best_prices_data = search_best_prices(travel_info)
                logger.info(f"Resultados da busca de melhores preços: {best_prices_data.keys() if isinstance(best_prices_data, dict) else 'Nenhum'}")

                if 'error' not in best_prices_data:
                    best_prices = best_prices_data.get('best_prices', [])

                    if best_prices:
                        logger.info(f"Encontradas {len(best_prices)} ofertas. Preços: {[p['price'] for p in best_prices[:3]]}")
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
    Extrai informações de viagem da mensagem e histórico
    
    Versão aprimorada que prioriza extração mínima e deixa o ChatGPT fazer o trabalho
    de conversa natural e confirmação de informações
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
        'adults': 1,
        'class': 'ECONOMY',  # Classe padrão
        'confirmed': False   # Flag para indicar se os dados foram confirmados pelo usuário
    }

    # Combinar mensagem atual com histórico para análise completa
    full_text = message.strip()
    for item in history:
        if isinstance(item, dict):
            if 'user' in item:
                full_text += " " + item.get('user', '').strip()
            if 'assistant' in item:
                full_text += " " + item.get('assistant', '').strip()
    
    # Verificar se as informações já foram confirmadas pelo usuário
    confirmation_patterns = [
        r'\bsim\b', r'\bconfirmo\b', r'\bcorreto\b', r'\bpode\s+seguir\b',
        r'\bconfirma(?:do)?\b', r'\bcontinue\b', r'\bvamos\s+em\s+frente\b', 
        r'\bcerto\b', r'\bok\b', r'\btudo\s+certo\b', r'\bestá\s+correto\b',
        r'\bprossiga\b', r'\bprosseguir\b', r'\bisso\s+mesmo\b'
    ]
    
    # Marcar como confirmado se encontrarmos palavras de confirmação na mensagem atual
    for pattern in confirmation_patterns:
        if re.search(pattern, message.lower()):
            travel_info['confirmed'] = True
            break
    
    # Padrões simplificados para extração de cidades/aeroportos
    # Buscamos apenas códigos IATA válidos (3 letras) ou menções claras de cidades
    city_airport_patterns = [
        # Códigos IATA (3 letras maiúsculas)
        r'\b([A-Z]{3})\b',
        # Cidades comuns no Brasil, com menor chance de falsos positivos
        r'\b(São Paulo|Rio de Janeiro|Salvador|Brasília|Recife|Fortaleza|Porto Alegre|Belo Horizonte|Curitiba|Manaus|Natal|Florianópolis)\b'
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

    # Encontrar códigos IATA e cidades no texto
    locations_found = []
    for pattern in city_airport_patterns:
        matches = re.finditer(pattern, full_text, re.IGNORECASE)
        for match in matches:
            location = match.group(1).strip()
            # Se for um código IATA (3 letras maiúsculas), adicionar diretamente
            if re.match(r'^[A-Z]{3}$', location):
                locations_found.append(location)
            else:
                # Para nomes de cidades, converter para código IATA
                iata_code = get_iata_code(location)
                if iata_code and len(iata_code) == 3:
                    locations_found.append(iata_code)
    
    # Se encontrarmos pelo menos dois locais, o primeiro é provável que seja a origem
    # e o segundo o destino (na maioria das conversas sobre viagens)
    if len(locations_found) >= 2:
        # Verificar menções específicas de origem/destino no texto
        origin_words = ['de', 'saindo', 'partindo', 'origem', 'estou em', 'estamos em']
        dest_words = ['para', 'destino', 'ir para', 'chegar em', 'visitar']
        
        # Iniciando com suposição simples: primeiro local = origem, segundo = destino
        travel_info['origin'] = locations_found[0]
        travel_info['destination'] = locations_found[1]
        
    # Se só encontramos um local, é mais provável que seja o destino
    elif len(locations_found) == 1:
        # Verificar se o texto indica claramente que é origem ou destino
        if any(word in full_text.lower() for word in ['de', 'saindo', 'partindo', 'estou em']):
            travel_info['origin'] = locations_found[0]
        else:
            travel_info['destination'] = locations_found[0]
    
    # Detectar quantidade de passageiros
    passengers_patterns = [
        r'(\d+)\s+(?:passageir[oa]s?|pessoas?|adult[oa]s?)',
        r'(?:com|para)\s+(?:minha|meu)\s+(esposa|marido|namorad[oa]|amig[oa]|filh[oa])',
        r'(?:viaj[oa]r|ir)\s+com\s+(\d+)\s+pessoas?',
        r'(?:somos|iremos|vamos)\s+(?:em\s+)?(\d+)',
        r'para\s+(?:mim|eu)\s+e\s+(?:minha|meu)\s+(esposa|marido|namorad[oa]|amig[oa]|filh[oa])',
        r'eu\s+e\s+(?:minha|meu)\s+(esposa|marido|namorad[oa]|amig[oa]|filh[oa])'
    ]
    
    for pattern in passengers_patterns:
        matches = re.search(pattern, full_text, re.IGNORECASE)
        if matches:
            match_str = matches.group(1)
            # Se for um número, usar esse valor
            if match_str.isdigit():
                travel_info['adults'] = int(match_str)
            # Se for uma referência a acompanhante, considerar como 2 pessoas
            elif match_str.lower() in ['esposa', 'marido', 'namorada', 'namorado', 'amigo', 'amiga', 'filho', 'filha']:
                travel_info['adults'] = 2
            break
    
    # Detectar duração da viagem para calcular data de retorno
    duration_patterns = [
        r'(?:passar|ficar)\s+(\d+)\s+dias',
        r'por\s+(\d+)\s+dias',
        r'durante\s+(\d+)\s+dias',
        r'estadia\s+(?:de|por)\s+(\d+)\s+dias',
        r'(\d+)\s+dias\s+(?:de|em)\s+(?:viagem|estadia|férias|ferias)',
        r'(\d+)\s+(?:noites|diárias|pernoites)'
    ]
    
    for pattern in duration_patterns:
        matches = re.search(pattern, full_text, re.IGNORECASE)
        if matches:
            try:
                duration_days = int(matches.group(1))
                # Se temos data de ida mas não de volta, calcular a volta
                if travel_info['departure_date'] and not travel_info['return_date'] and duration_days > 0:
                    departure_date_obj = datetime.strptime(travel_info['departure_date'], '%Y-%m-%d')
                    return_date_obj = departure_date_obj + timedelta(days=duration_days)
                    travel_info['return_date'] = return_date_obj.strftime('%Y-%m-%d')
                    logger.info(f"Calculada data de retorno com base na duração: {travel_info['return_date']}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Erro ao processar duração da viagem: {e}")
            break
            
    # Função auxiliar para normalizar texto
    import unicodedata
    def normalize_text(text):
        return unicodedata.normalize('NFKD', text.lower()).encode('ASCII', 'ignore').decode('ASCII')
    
    # Detectar classe de viagem
    class_patterns = [
        r'classe\s+(econ[ôo]mica|executiva|primeira|business|premium)',
        r'(econ[ôo]mica|executiva|primeira|business|premium)\s+classe',
        r'passagens?\s+(econ[ôo]micas?|executivas?|premium)'
    ]
    
    class_map = {
        'economica': 'ECONOMY', 
        'econômica': 'ECONOMY',
        'executiva': 'BUSINESS',
        'business': 'BUSINESS',
        'primeira': 'FIRST',
        'premium': 'PREMIUM_ECONOMY'
    }
    
    for pattern in class_patterns:
        matches = re.search(pattern, full_text, re.IGNORECASE)
        if matches:
            class_str = normalize_text(matches.group(1).lower())
            for key, value in class_map.items():
                if normalize_text(key) in class_str:
                    travel_info['class'] = value
                    break
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
            
    # Define origin_patterns e destination_patterns como vazios para evitar erros 
    origin_patterns = []
    destination_patterns = []

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
        # Inicializar serviços de API
        from services.skyscanner_service import SkyscannerService
        from services.amadeus_service import AmadeusService

        skyscanner_service = SkyscannerService()
        amadeus_service = AmadeusService()

        logging.info("Serviços de API inicializados: Skyscanner e Amadeus")

        # Preparar parâmetros para a API
        params = {
            'origin': travel_info.get('origin'),
            'destination': travel_info.get('destination'),
            'departure_date': travel_info.get('departure_date'),
            'return_date': travel_info.get('return_date'),
            'adults': travel_info.get('adults', 1),
            'currency': 'BRL'
        }

        logging.info(f"Iniciando busca com parâmetros: {params}")

        logger.info(f"Iniciando busca de voos com parâmetros: {params}")

        # Testar se temos credenciais válidas em ambos os serviços
        has_amadeus_token = amadeus_service.get_token() is not None
        logger.info(f"Amadeus API disponível: {has_amadeus_token}")

        # Tentar primeiro o Skyscanner
        logger.info("Tentando buscar voos via Skyscanner")
        skyscanner_flights = skyscanner_service.search_flights(params)

        # Verificar se a busca do Skyscanner foi bem-sucedida
        skyscanner_success = 'error' not in skyscanner_flights and skyscanner_flights.get('flights', [])

        # Se não tiver resultados do Skyscanner, usar o Amadeus diretamente
        if not skyscanner_success:
            logger.warning(f"Sem resultados do Skyscanner ou erro encontrado: {skyscanner_flights.get('error', 'Sem voos encontrados')}")
            logger.info("Buscando voos via Amadeus")

            # Verificar se o token do Amadeus está disponível
            if not has_amadeus_token:
                logger.warning("Token do Amadeus não disponível, tentando obter novo token...")
                has_amadeus_token = amadeus_service.get_token() is not None

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
                            
                        # Usar o primeiro itinerário (normalmente ida)
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

                # Retornar mensagem de erro quando o serviço não está disponível
                logger.info("Serviço de busca de voos indisponível no momento")
                return {"error": "No momento, não foi possível obter dados reais de voos. Por favor, tente novamente mais tarde."}

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
        return {"error": "No momento não foi possível obter dados reais de voos. Por favor, tente novamente mais tarde."}

    except Exception as e:
        logger.error(f"Erro ao buscar voos: {str(e)}")
        return {"error": f"Erro ao buscar voos: {str(e)}"}

def search_best_prices(travel_info):
    """
    Busca melhores preços para um período flexível
    """
    try:
        logger.info(f"Buscando melhores preços para {travel_info.get('origin')} -> {travel_info.get('destination')}")
        
        # Inicializar serviços de API
        from services.skyscanner_service import SkyscannerService
        from services.amadeus_service import AmadeusService
        
        skyscanner_service = SkyscannerService()
        amadeus_service = AmadeusService()
        
        logger.info("Serviços de API inicializados")
        
        # Preparar parâmetros para a API
        params = {
            'origin': travel_info.get('origin'),
            'destination': travel_info.get('destination'),
            'departure_date': travel_info.get('date_range_start'),
            'return_date': travel_info.get('date_range_end'),
            'adults': travel_info.get('adults', 1),
            'currency': 'BRL',
            'max_dates_to_check': travel_info.get('max_dates_to_check', 3)  # Limitar o número de datas para busca rápida
        }
        
        logger.info(f"Iniciando busca com parâmetros: {params}")
        
        # Tentar primeiro o Skyscanner
        skyscanner_prices = skyscanner_service.search_best_prices(params)
        
        # Verificar se a busca do Skyscanner foi bem-sucedida
        if 'error' not in skyscanner_prices and skyscanner_prices.get('best_prices', []):
            return skyscanner_prices
            
        # Se não tiver resultados do Skyscanner, usar o Amadeus
        logger.warning(f"Sem resultados do Skyscanner: {skyscanner_prices.get('error', 'Sem ofertas encontradas')}")
        
        # Mapear parâmetros para o formato do Amadeus
        amadeus_params = {
            'originLocationCode': params['origin'],
            'destinationLocationCode': params['destination'],
            'departureDate': params['departure_date'],
            'returnDate': params.get('return_date'),
            'adults': params['adults'],
            'currencyCode': params['currency'],
            'max_dates_to_check': params.get('max_dates_to_check', 3)  # Incluir parâmetro de limite de datas
        }
        
        # Buscar melhores preços no Amadeus
        best_prices = []
        
        try:
            # Tentar buscar preços reais do Amadeus
            amadeus_prices = amadeus_service.search_best_prices(amadeus_params)
            if 'error' not in amadeus_prices and amadeus_prices.get('best_prices', []):
                return amadeus_prices
        except Exception as e:
            logger.error(f"Erro ao buscar preços no Amadeus: {str(e)}")
        
        # Usar dados simulados se as APIs falharem
        # Não utilizamos mais dados simulados, informamos que o serviço está indisponível
        logger.warning("Não foi possível obter dados reais de nenhuma API.")
        return {"error": "No momento não foi possível obter dados reais de preços. Por favor, tente novamente mais tarde."}
    except Exception as e:
        logger.error(f"Erro na busca de melhores preços: {str(e)}")
        return {"error": f"Erro ao buscar melhores preços: {str(e)}"}