"""
Processador de mensagens do chat para extração de informações de viagem e interação com APIs
"""

import os
import json
import logging
import uuid
import re
from datetime import datetime, timedelta
import requests

from services.flight_service_connector import flight_service_connector

# Configurar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatProcessor:
    """
    Processa mensagens do chat, extrai informações de viagem
    e interage com APIs externas para obter dados reais
    """
    
    def __init__(self):
        """Inicializa o processador de chat"""
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.sessions = {}  # Armazena informações das sessões de chat
        
    def validate_travel_info(self, travel_info):
        """
        Verifica se as informações de viagem são suficientes para busca
        
        Args:
            travel_info: Dicionário com informações de viagem
            
        Returns:
            dict: Dicionário de erros (vazio se não houver erros)
        """
        errors = {}
        
        # Verificar origem
        if not travel_info.get('origin'):
            errors['origin'] = 'Origem da viagem não informada'
            
        # Verificar destino
        if not travel_info.get('destination'):
            errors['destination'] = 'Destino da viagem não informado'
            
        # Verificar datas
        if not travel_info.get('departure_date') and not travel_info.get('date_range_start'):
            errors['date'] = 'Data da viagem não informada'
            
        return errors
    
    def format_travel_info_summary(self, travel_info):
        """
        Formata um resumo das informações de viagem para apresentação
        
        Args:
            travel_info: Dicionário com informações de viagem
            
        Returns:
            str: Resumo formatado das informações
        """
        summary = []
        
        # Adicionar origem
        if travel_info.get('origin'):
            summary.append(f"Origem: {travel_info.get('origin')}")
            
        # Adicionar destino
        if travel_info.get('destination'):
            summary.append(f"Destino: {travel_info.get('destination')}")
            
        # Adicionar data de ida
        if travel_info.get('departure_date_formatted'):
            summary.append(f"Data de ida: {travel_info.get('departure_date_formatted')}")
        elif travel_info.get('departure_date'):
            summary.append(f"Data de ida: {travel_info.get('departure_date')}")
            
        # Adicionar data de volta
        if travel_info.get('return_date_formatted'):
            summary.append(f"Data de volta: {travel_info.get('return_date_formatted')}")
        elif travel_info.get('return_date'):
            summary.append(f"Data de volta: {travel_info.get('return_date')}")
            
        # Adicionar número de passageiros
        if travel_info.get('adults'):
            summary.append(f"Passageiros: {travel_info.get('adults')} adulto(s)")
            
        return "\n".join(summary)
    
    def get_flight_search_intro(self, origin, destination):
        """
        Gera uma introdução amigável para os resultados de voo
        
        Args:
            origin: Código do aeroporto de origem
            destination: Código do aeroporto de destino
            
        Returns:
            str: Introdução para os resultados de voo
        """
        return f"Estou buscando as melhores opções de voo de {origin} para {destination}..."
    
    def format_error_message(self, error_message):
        """
        Formata uma mensagem de erro para apresentação ao usuário
        
        Args:
            error_message: Mensagem de erro original
            
        Returns:
            str: Mensagem de erro formatada
        """
        return f"Desculpe, tive um problema na busca: {error_message}"
    
    def process_message(self, message, user_id=None, conversation_id=None):
        """
        Processa uma mensagem do usuário, extrai informações de viagem
        e obtém dados reais quando necessário
        
        Args:
            message: Texto da mensagem do usuário
            user_id: ID do usuário (opcional)
            conversation_id: ID da conversa (opcional)
            
        Returns:
            dict: Resposta processada para o usuário
        """
        try:
            # Gerar um ID de sessão se não for fornecido
            session_id = conversation_id or str(uuid.uuid4())
            
            # Extrair informações de viagem da mensagem
            travel_info = self.extract_travel_info(message)
            logger.info(f"Informações de viagem extraídas: {travel_info}")
            
            # Verificar se temos informações suficientes para buscar voos
            if self._can_search_flights(travel_info):
                logger.info(f"Informações suficientes para buscar voos na sessão {session_id}")
                
                # Buscar voos reais
                flight_data = self._search_real_flights(travel_info, session_id)
                
                # Se a busca por período flexível estiver habilitada, buscar também os melhores preços
                best_prices_data = None
                if travel_info.get("flexible_dates", False):
                    best_prices_data = self._search_best_prices(travel_info, session_id)
                
                # Formatar os resultados para o chat (adaptado para a versão atual da API)
                # Versão simplificada já que o painel lateral substitui a funcionalidade
                response = {
                    "message": "Encontrei algumas opções de voos para você! Verifique o painel lateral.",
                    "show_flight_results": True,
                    "session_id": session_id
                }
                
                # Adicionar o ID da sessão à resposta para garantir que o mural funcione
                response['session_id'] = session_id
                
                # Verificar se podemos mostrar resultados
                if flight_data and "error" not in flight_data and "data" in flight_data and flight_data["data"]:
                    # Definir flag para mostrar o mural de resultados
                    response['show_flight_results'] = True
                    
                    # Disparar evento para mostrar o mural de resultados
                    logger.info(f"Preparando para mostrar resultados de voo para sessão {session_id}")
                    
                    return response
            
            # Se não pudermos buscar voos ou ocorrer um erro, usar o GPT para gerar uma resposta
            gpt_response = self._generate_gpt_response(message, travel_info, session_id)
            return gpt_response
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            return {
                "message": "Desculpe, tive um problema ao processar sua solicitação. Por favor, tente novamente."
            }
    
    def extract_travel_info(self, message):
        """
        Extrai informações de viagem de uma mensagem usando regras e expressões regulares
        
        Args:
            message: Texto da mensagem do usuário
            
        Returns:
            dict: Informações extraídas sobre a viagem
        """
        # Inicializar dicionário de informações
        info = {
            "origin": None,
            "destination": None,
            "departure_date": None,
            "return_date": None,
            "adults": 1,
            "flexible_dates": False
        }
        
        # Lista de cidades brasileiras comuns e seus códigos IATA
        cities = {
            "são paulo": "GRU",
            "sao paulo": "GRU",
            "sampa": "GRU",
            "rio de janeiro": "GIG", 
            "rio": "GIG",
            "brasília": "BSB",
            "brasilia": "BSB",
            "salvador": "SSA",
            "recife": "REC",
            "fortaleza": "FOR",
            "belo horizonte": "CNF",
            "belém": "BEL",
            "belem": "BEL",
            "porto alegre": "POA",
            "manaus": "MAO",
            "curitiba": "CWB",
            "goiânia": "GYN",
            "goiania": "GYN",
            "natal": "NAT",
            "florianópolis": "FLN",
            "florianopolis": "FLN",
            "miami": "MIA",
            "nova york": "JFK",
            "nova iorque": "JFK",
            "new york": "JFK",
            "paris": "CDG",
            "londres": "LHR",
            "london": "LHR",
            "roma": "FCO",
            "roma": "FCO",
            "madrid": "MAD",
            "tóquio": "HND",
            "toquio": "HND",
            "tokyo": "HND",
            "buenos aires": "EZE",
            "santiago": "SCL"
        }
        
        # Buscar cidades na mensagem
        found_cities = []
        for city, code in cities.items():
            if city.lower() in message.lower():
                found_cities.append((city, code))
        
        # Se encontrou pelo menos duas cidades, assumir origem e destino
        if len(found_cities) >= 2:
            info["origin"] = found_cities[0][1]  # código IATA
            info["destination"] = found_cities[1][1]  # código IATA
        
        # Buscar datas na mensagem
        # Formato: DD/MM/YYYY ou DD-MM-YYYY ou DD de mes de YYYY
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{1,2}) de (janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro) de (\d{4})'  # DD de mes de YYYY
        ]
        
        found_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, message.lower())
            for match in matches:
                if len(match) == 3:
                    if match[1] in ["janeiro", "fevereiro", "março", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]:
                        # Converter nome do mês para número
                        month_names = {
                            "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
                            "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
                            "outubro": 10, "novembro": 11, "dezembro": 12
                        }
                        month = month_names[match[1]]
                        day = int(match[0])
                        year = int(match[2])
                    else:
                        day = int(match[0])
                        month = int(match[1])
                        year = int(match[2])
                    
                    # Verificar se a data é válida
                    try:
                        date = datetime(year, month, day)
                        if date >= datetime.now():  # Somente datas futuras
                            found_dates.append(date.strftime("%Y-%m-%d"))
                    except ValueError:
                        pass
        
        # Se encontrou pelo menos uma data, assumir como data de ida
        if found_dates:
            info["departure_date"] = found_dates[0]
            logger.info(f"Encontrada data específica: {info['departure_date']}")
            
            # Se encontrou duas datas, a segunda é a volta
            if len(found_dates) >= 2:
                info["return_date"] = found_dates[1]
            else:
                # Verificar menções a duração da viagem
                duration_patterns = [
                    r'(\d+)\s*dias',
                    r'(\d+)\s*semanas'
                ]
                
                for pattern in duration_patterns:
                    match = re.search(pattern, message.lower())
                    if match:
                        value = int(match.group(1))
                        if "semanas" in match.group(0):
                            value *= 7
                        
                        logger.info(f"Detectada menção a estadia de {value} dias")
                        
                        # Calcular data de retorno
                        departure = datetime.strptime(info["departure_date"], "%Y-%m-%d")
                        return_date = departure + timedelta(days=value)
                        info["return_date"] = return_date.strftime("%Y-%m-%d")
                        logger.info(f"Calculada data de retorno baseada em {value} dias: {info['return_date']}")
                        break
        
        # Verificar menções a período flexível
        if re.search(r'flex[ií]vel|qualquer data|qualquer momento|melhor[es]? pre[çc]os?', message.lower()):
            info["flexible_dates"] = True
        
        # Verificar menção a número de passageiros
        passengers_match = re.search(r'(\d+)\s*(?:adultos?|pessoas?|passageiros?)', message.lower())
        if passengers_match:
            info["adults"] = min(9, int(passengers_match.group(1)))  # Máximo de 9 adultos
        
        return info
    
    def _can_search_flights(self, travel_info):
        """
        Verifica se temos informações suficientes para buscar voos reais
        
        Args:
            travel_info: Dicionário com informações de viagem
            
        Returns:
            bool: True se podemos buscar voos, False caso contrário
        """
        # Precisamos pelo menos de origem, destino e data de ida
        return (
            travel_info.get("origin") and 
            travel_info.get("destination") and 
            travel_info.get("departure_date")
        )
    
    def _search_real_flights(self, travel_info, session_id):
        """
        Busca voos reais com base nas informações extraídas
        
        Args:
            travel_info: Dicionário com informações de viagem
            session_id: ID da sessão de chat
            
        Returns:
            dict: Dados de voos reais
        """
        try:
            # Extrair parâmetros para a busca
            origin = travel_info["origin"]
            destination = travel_info["destination"]
            departure_date = travel_info["departure_date"]
            return_date = travel_info.get("return_date")
            adults = travel_info.get("adults", 1)
            
            # Buscar voos usando o serviço de conexão com a API Amadeus
            flight_data = flight_service_connector.search_flights_from_chat(
                travel_info={
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "adults": adults,
                    "currency": "BRL"
                },
                session_id=session_id
            )
            
            return flight_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar voos reais: {str(e)}")
            return {"error": f"Erro ao buscar voos: {str(e)}"}
    
    def _search_best_prices(self, travel_info, session_id):
        """
        Busca os melhores preços para um período flexível
        
        Args:
            travel_info: Dicionário com informações de viagem
            session_id: ID da sessão de chat
            
        Returns:
            dict: Dados de melhores preços
        """
        try:
            # Extrair parâmetros para a busca
            origin = travel_info["origin"]
            destination = travel_info["destination"]
            
            # Se temos datas específicas, usar como base para o período
            if travel_info["departure_date"]:
                departure_date = datetime.strptime(travel_info["departure_date"], "%Y-%m-%d")
                
                # Definir período de 15 dias em torno da data solicitada
                date_range_start = (departure_date - timedelta(days=7)).strftime("%Y-%m-%d")
                date_range_end = (departure_date + timedelta(days=7)).strftime("%Y-%m-%d")
                
                # Se temos data de retorno, ajustar o período final
                if travel_info.get("return_date"):
                    return_date = datetime.strptime(travel_info["return_date"], "%Y-%m-%d")
                    date_range_end = (return_date + timedelta(days=7)).strftime("%Y-%m-%d")
            else:
                # Se não temos datas específicas, usar período padrão
                today = datetime.now()
                date_range_start = today.strftime("%Y-%m-%d")
                date_range_end = (today + timedelta(days=30)).strftime("%Y-%m-%d")
            
            # NOTA: A busca de melhores preços foi movida para o painel lateral
            # Esta seção é mantida para compatibilidade mas não executa mais uma busca real
            # já que o painel lateral faz isso automaticamente
            best_prices_data = {
                "origin": origin,
                "destination": destination,
                "date_range": f"{date_range_start} a {date_range_end}",
                "message": "Busca movida para o painel lateral",
                "best_prices": []
            }
            
            return best_prices_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar melhores preços: {str(e)}")
            return {"error": f"Erro ao buscar melhores preços: {str(e)}"}
    
    def _generate_gpt_response(self, message, travel_info, session_id):
        """
        Gera uma resposta usando a API do GPT quando não podemos 
        ou não precisamos buscar dados reais
        
        Args:
            message: Mensagem original do usuário
            travel_info: Informações de viagem extraídas
            session_id: ID da sessão
            
        Returns:
            dict: Resposta gerada para o chat
        """
        try:
            # Verificar se temos a chave da API
            if not self.openai_api_key:
                return {
                    "message": "Estou com um problema para processar seu pedido agora. "
                               "Por favor, tente novamente mais tarde."
                }
            
            # Para este exemplo, retornamos uma resposta estática
            # Em um sistema real, você chamaria a API do GPT aqui
            return {
                "message": "Entendi seu pedido! Para eu poder ajudar com informações de voos, "
                           "preciso de alguns detalhes específicos como a cidade de origem, "
                           "destino e data da viagem. Por favor, me informe esses dados para "
                           "que eu possa buscar as melhores opções para você."
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta GPT: {str(e)}")
            return {
                "message": "Desculpe, tive um problema ao processar sua solicitação. "
                           "Por favor, tente novamente."
            }


# Instância global para uso em toda a aplicação
chat_processor = ChatProcessor()