
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
        
        # Extrair parâmetros da mensagem via OpenAI
        params = extract_flight_params(message, history)
        
        # Se não conseguiu extrair parâmetros suficientes, solicitar mais informações
        if not params or params.get('error'):
            # Preparar o contexto específico para busca rápida
            system_context = BUSCA_RAPIDA_PROMPT
            
            # Chamar o assistente da OpenAI para obter mais informações
            result = openai_service.travel_assistant(
                user_message=message,
                conversation_history=history,
                system_context=system_context
            )
            
            # Verificar se houve erro na chamada à API
            if 'error' in result:
                logger.error(f"Erro ao chamar a API OpenAI: {result['error']}")
                return {"error": True, "message": "Erro ao processar sua mensagem. Por favor, tente novamente em alguns instantes."}
            
            # Retornar a resposta do assistente solicitando mais informações
            return {"response": result.get('response', '')}
        
        # Se temos parâmetros suficientes, buscar voos
        logger.info(f"Parâmetros extraídos: {json.dumps(params)}")
        
        # Buscar voos com o serviço do Skyscanner
        flights_result = skyscanner_service.get_mock_flights(params)  # Usar mock para testes
        # flights_result = skyscanner_service.search_flights(params)  # Em produção
        
        if 'error' in flights_result:
            logger.error(f"Erro ao buscar voos: {flights_result['error']}")
            error_response = f"Desculpe, não consegui encontrar voos com os parâmetros informados. " \
                            f"Erro: {flights_result.get('error', 'Erro desconhecido')}"
            return {"response": error_response}
        
        # Formatar resposta com os resultados dos voos
        response = format_flight_response(params, flights_result)
        
        return response
        
    except Exception as e:
        logger.exception(f"Erro ao processar mensagem no modo busca rápida: {str(e)}")
        return {"error": True, "message": f"Ocorreu um erro inesperado: {str(e)}"}

def extract_flight_params(message, history):
    """
    Extrai parâmetros de voo da mensagem do usuário
    
    Args:
        message (str): Mensagem do usuário
        history (list): Histórico de conversa
        
    Returns:
        dict: Parâmetros de voo extraídos
    """
    try:
        # Combinar histórico e mensagem atual
        full_context = "\n".join([msg.get('content', '') for msg in history]) + "\n" + message
        
        # Usar regex para extrair informações comuns
        params = {}
        
        # Extração de códigos IATA (3 letras maiúsculas para aeroportos)
        origin_match = re.search(r'\b([A-Z]{3})\s+(?:para|to|->)\s+([A-Z]{3})\b', full_context.upper())
        if origin_match:
            params['origin'] = origin_match.group(1)
            params['destination'] = origin_match.group(2)
        
        # Extração de nomes de cidades comuns
        cities_map = {
            'SÃO PAULO': 'GRU', 'SAO PAULO': 'GRU', 'SP': 'GRU', 'GUARULHOS': 'GRU', 'CONGONHAS': 'CGH',
            'RIO DE JANEIRO': 'GIG', 'RIO': 'GIG', 'GALEÃO': 'GIG', 'SANTOS DUMONT': 'SDU',
            'BRASÍLIA': 'BSB', 'BRASILIA': 'BSB',
            'SALVADOR': 'SSA',
            'RECIFE': 'REC',
            'FORTALEZA': 'FOR',
            'PORTO ALEGRE': 'POA',
            'CURITIBA': 'CWB',
            'BELÉM': 'BEL', 'BELEM': 'BEL',
            'MANAUS': 'MAO',
            'MIAMI': 'MIA', 'ORLANDO': 'MCO', 'NOVA YORK': 'JFK', 'NEW YORK': 'JFK',
            'LISBOA': 'LIS', 'MADRID': 'MAD', 'LONDRES': 'LHR', 'LONDON': 'LHR',
            'PARIS': 'CDG', 'ROMA': 'FCO', 'ROME': 'FCO',
            'TÓQUIO': 'HND', 'TOKYO': 'HND'
        }
        
        # Buscar cidades no mapa
        for city, code in cities_map.items():
            if city in full_context.upper():
                # Determinar se é origem ou destino
                if 'DE ' + city in full_context.upper() or 'FROM ' + city in full_context.upper():
                    params['origin'] = code
                elif 'PARA ' + city in full_context.upper() or 'TO ' + city in full_context.upper() or 'EM ' + city in full_context.upper():
                    params['destination'] = code
                # Se não está claro, assume que é destino
                elif 'destination' not in params:
                    params['destination'] = code
        
        # Extração de datas
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # DD/MM/YYYY ou DD-MM-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'     # YYYY/MM/DD ou YYYY-MM-DD
        ]
        
        found_dates = []
        
        for pattern in date_patterns:
            dates = re.findall(pattern, full_context)
            for date_parts in dates:
                try:
                    if len(date_parts[2]) == 4:  # DD/MM/YYYY
                        date_obj = datetime(int(date_parts[2]), int(date_parts[1]), int(date_parts[0]))
                    else:  # YYYY/MM/DD
                        date_obj = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                    
                    found_dates.append(date_obj.strftime("%Y-%m-%d"))
                except ValueError:
                    # Data inválida, ignorar
                    pass
        
        # Determinar datas de ida e volta
        if len(found_dates) >= 1:
            if len(found_dates) >= 2:
                # Ordenar datas
                found_dates.sort()
                params['departureDate'] = found_dates[0]
                params['returnDate'] = found_dates[1]
            else:
                params['departureDate'] = found_dates[0]
        
        # Se não temos uma data de partida, usar data atual + 7 dias como padrão
        if 'departureDate' not in params:
            future_date = datetime.now() + timedelta(days=7)
            params['departureDate'] = future_date.strftime("%Y-%m-%d")
        
        # Verificar se temos parâmetros mínimos
        if 'destination' not in params:
            return {'error': 'Destino não identificado'}
        
        # Padrões para origem
        if 'origin' not in params:
            # Definir GRU (São Paulo) como origem padrão para o mercado brasileiro
            params['origin'] = 'GRU'
        
        # Número de adultos, padrão 1
        params['adults'] = 1
        
        return params
        
    except Exception as e:
        logger.exception(f"Erro ao extrair parâmetros de voo: {str(e)}")
        return {'error': f"Erro ao extrair parâmetros: {str(e)}"}

def format_flight_response(params, flights_result):
    """
    Formata a resposta com os resultados dos voos
    
    Args:
        params (dict): Parâmetros da busca
        flights_result (dict): Resultados dos voos
        
    Returns:
        dict: Resposta formatada
    """
    try:
        # Obter principais variáveis
        origin = params.get('origin', '')
        destination = params.get('destination', '')
        departure_date = params.get('departureDate', '')
        return_date = params.get('returnDate', '')
        
        flights = flights_result.get('flights', [])
        currency = flights_result.get('currency', 'BRL')
        avg_price = flights_result.get('avg_price', None)
        min_price = flights_result.get('min_price', None)
        
        if not flights:
            return {
                "response": "Não encontrei voos disponíveis para os parâmetros informados. " 
                            "Por favor, tente datas alternativas ou outros aeroportos."
            }
        
        # Calcular datas em formato legível
        dep_date_obj = datetime.strptime(departure_date, "%Y-%m-%d")
        dep_date_formatted = dep_date_obj.strftime("%d/%m/%Y")
        
        ret_date_formatted = ""
        if return_date:
            ret_date_obj = datetime.strptime(return_date, "%Y-%m-%d")
            ret_date_formatted = ret_date_obj.strftime("%d/%m/%Y")
        
        # Pegar o voo mais barato
        best_flight = flights[0]
        best_price = best_flight['price']
        
        # Preparar link de afiliado
        affiliate_link = best_flight.get('deeplink', {}).get('url', '')
        if not affiliate_link:
            affiliate_link = skyscanner_service.generate_affiliate_link(destination, departure_date, return_date)
        
        # Análise de preço
        price_analysis = ""
        if avg_price and best_price:
            diff_percent = ((best_price / avg_price) - 1) * 100
            
            if diff_percent <= -15:
                price_analysis = "Este preço está muito abaixo da média! É uma excelente oportunidade para comprar."
            elif diff_percent <= -5:
                price_analysis = "Este preço está abaixo da média. Boa oportunidade para comprar."
            elif diff_percent <= 5:
                price_analysis = "Este preço está na média do mercado para esta rota."
            elif diff_percent <= 15:
                price_analysis = "Este preço está um pouco acima da média. Considere verificar outras datas."
            else:
                price_analysis = "Este preço está significativamente acima da média. Recomendo verificar outras datas ou companhias."
        
        # Construir resposta
        response_text = f"Encontrei as seguintes opções de voo de {origin} para {destination}:\n\n"
        response_text += f"🔍 **Melhor oferta**\n"
        
        # Informações do voo de ida
        if best_flight.get('legs') and len(best_flight['legs']) > 0:
            ida_leg = best_flight['legs'][0]
            
            # Extrair companhia aérea
            airline = ""
            if ida_leg.get('segments') and len(ida_leg['segments']) > 0:
                airline = ida_leg['segments'][0].get('carrier', '')
            
            # Formatar horários
            dep_time = "Não informado"
            arr_time = "Não informado"
            
            if ida_leg.get('departure', {}).get('time'):
                try:
                    dep_datetime = datetime.strptime(ida_leg['departure']['time'], "%Y-%m-%dT%H:%M:%S")
                    dep_time = dep_datetime.strftime("%H:%M")
                except:
                    pass
            
            if ida_leg.get('arrival', {}).get('time'):
                try:
                    arr_datetime = datetime.strptime(ida_leg['arrival']['time'], "%Y-%m-%dT%H:%M:%S")
                    arr_time = arr_datetime.strftime("%H:%M")
                except:
                    pass
            
            # Duração do voo
            duration = ida_leg.get('duration', 0)
            duration_hours = duration // 60
            duration_mins = duration % 60
            duration_formatted = f"{duration_hours}h{duration_mins:02d}min"
            
            # Escalas
            stops = ida_leg.get('stops', 0)
            stops_text = "Voo direto" if stops == 0 else f"{stops} escala{'s' if stops > 1 else ''}"
            
            response_text += f"✈️ **Ida ({dep_date_formatted})**: {airline} - {dep_time} → {arr_time} ({duration_formatted})\n"
            response_text += f"📍 {origin} → {destination} - {stops_text}\n"
        
        # Informações do voo de volta (se houver)
        if best_flight.get('legs') and len(best_flight['legs']) > 1 and return_date:
            volta_leg = best_flight['legs'][1]
            
            # Extrair companhia aérea
            airline = ""
            if volta_leg.get('segments') and len(volta_leg['segments']) > 0:
                airline = volta_leg['segments'][0].get('carrier', '')
            
            # Formatar horários
            dep_time = "Não informado"
            arr_time = "Não informado"
            
            if volta_leg.get('departure', {}).get('time'):
                try:
                    dep_datetime = datetime.strptime(volta_leg['departure']['time'], "%Y-%m-%dT%H:%M:%S")
                    dep_time = dep_datetime.strftime("%H:%M")
                except:
                    pass
            
            if volta_leg.get('arrival', {}).get('time'):
                try:
                    arr_datetime = datetime.strptime(volta_leg['arrival']['time'], "%Y-%m-%dT%H:%M:%S")
                    arr_time = arr_datetime.strftime("%H:%M")
                except:
                    pass
            
            # Duração do voo
            duration = volta_leg.get('duration', 0)
            duration_hours = duration // 60
            duration_mins = duration % 60
            duration_formatted = f"{duration_hours}h{duration_mins:02d}min"
            
            # Escalas
            stops = volta_leg.get('stops', 0)
            stops_text = "Voo direto" if stops == 0 else f"{stops} escala{'s' if stops > 1 else ''}"
            
            response_text += f"✈️ **Volta ({ret_date_formatted})**: {airline} - {dep_time} → {arr_time} ({duration_formatted})\n"
            response_text += f"📍 {destination} → {origin} - {stops_text}\n"
        
        # Preço e análise
        response_text += f"\n💰 **Preço Total**: {currency} {best_price:.2f}\n"
        response_text += f"💡 **Análise de Preço**: {price_analysis}\n\n"
        
        # Link de compra
        if affiliate_link:
            response_text += "🔗 Para comprar esta passagem, [clique aqui]({{LINK_COMPRA}}). Você será redirecionado para o site da empresa aérea ou agência de viagens.\n\n"
            response_text += "Posso ajudar com mais alguma coisa? Se quiser verificar outras datas ou destinos, é só me informar."
        else:
            response_text += "Para comprar essa passagem, você pode visitar o site da companhia aérea ou de agências de viagens online como Skyscanner, Decolar, ou CVC.\n\n"
            response_text += "Posso ajudar com mais alguma coisa? Se quiser verificar outras datas ou destinos, é só me informar."
        
        response = {
            "response": response_text.replace("{{LINK_COMPRA}}", affiliate_link)
        }
        
        # Adicionar link de compra como um campo separado para o frontend
        if affiliate_link:
            response["purchase_link"] = affiliate_link
        
        return response
        
    except Exception as e:
        logger.exception(f"Erro ao formatar resposta de voos: {str(e)}")
        return {
            "response": "Desculpe, encontrei um problema ao formatar a resposta. "
                       f"Erro: {str(e)}"
        }
