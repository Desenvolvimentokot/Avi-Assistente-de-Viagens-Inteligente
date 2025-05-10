"""
Módulo para extrair dados de voos a partir de mensagens do chat
Esta classe analisa mensagens do usuário e extrai informações relevantes 
para iniciar uma busca oculta de voos.
"""

import re
import logging
from datetime import datetime, timedelta

# Configurar logger
logger = logging.getLogger(__name__)

class ChatFlightExtractor:
    """
    Extrai informações de voos a partir de mensagens do chat.
    Esta classe usa padrões de expressão regular para identificar
    origens, destinos e datas em mensagens de texto.
    """
    
    def __init__(self):
        # Inicializar dicionário de cidades e aeroportos conhecidos
        self.city_to_iata = {
            'são paulo': 'GRU',
            'sao paulo': 'GRU',
            'sampa': 'GRU',
            'rio de janeiro': 'GIG',
            'rio': 'GIG',
            'brasília': 'BSB', 
            'brasilia': 'BSB',
            'belo horizonte': 'CNF',
            'salvador': 'SSA',
            'recife': 'REC',
            'fortaleza': 'FOR',
            'curitiba': 'CWB',
            'manaus': 'MAO',
            'porto alegre': 'POA',
            'belém': 'BEL',
            'belem': 'BEL',
            'goiânia': 'GYN',
            'goiania': 'GYN',
            'joão pessoa': 'JPA',
            'joao pessoa': 'JPA',
            'maceió': 'MCZ',
            'maceio': 'MCZ',
            'florianópolis': 'FLN',
            'florianopolis': 'FLN',
            'natal': 'NAT',
            'vitória': 'VIX',
            'vitoria': 'VIX',
            'londres': 'LHR',
            'london': 'LHR',
            'nova york': 'JFK',
            'nova iorque': 'JFK',
            'new york': 'JFK',
            'paris': 'CDG',
            'tóquio': 'NRT',
            'toquio': 'NRT',
            'tokyo': 'NRT',
            'madri': 'MAD',
            'madrid': 'MAD',
            'lisboa': 'LIS',
            'lisbon': 'LIS',
            'roma': 'FCO',
            'rome': 'FCO',
            'miami': 'MIA',
            'orlando': 'MCO',
            'los angeles': 'LAX',
            'la': 'LAX',
            'chicago': 'ORD',
            'toronto': 'YYZ',
            'buenos aires': 'EZE',
            'santiago': 'SCL',
            'amsterdam': 'AMS',
            'berlim': 'BER',
            'berlin': 'BER',
            'barcelona': 'BCN',
            'dubai': 'DXB',
            'hong kong': 'HKG',
            'sydney': 'SYD',
            'frankfurt': 'FRA',
            'zurique': 'ZRH',
            'zurich': 'ZRH',
            'atenas': 'ATH',
            'athens': 'ATH',
            'bangkok': 'BKK',
            'pequim': 'PEK',
            'beijing': 'PEK',
            'istambul': 'IST',
            'istanbul': 'IST'
        }
        
        # Padrões para identificar origens e destinos
        self.origin_patterns = [
            r'(?:de|saindo de|partindo de|sa(í|i)r de|sair|partir|embarcar|origem)\s+(?:em\s+)?([a-zÀ-ú\s]+?)(?:\s+(?:para|com destino|destino|chegando em|at(é|e)))(?!\s+de\s+|\s+em\s+|\s+para\s+)',
            r'(?:de|saindo de|partindo de|sa(í|i)r de|sair|partir|embarcar|origem)\s+(?:em\s+)?([a-zÀ-ú\s]+?)(?:\s+(?:no dia|dia|na data|em|at(é|e)))(?!\s+de\s+|\s+em\s+|\s+para\s+)'
        ]
        
        self.destination_patterns = [
            r'(?:para|destino|indo para|com destino a|chegando em|at(é|e))\s+([a-zÀ-ú\s]+?)(?:\s+(?:no dia|dia|na data|em|at(é|e)))(?!\s+de\s+|\s+em\s+|\s+para\s+)',
            r'(?:para|destino|indo para|com destino a|chegando em|at(é|e))\s+(?:a cidade de\s+)?([a-zÀ-ú\s]+?)(?:\.|\s|$)(?!\s+de\s+|\s+em\s+|\s+para\s+)'
        ]
        
        # Padrões para identificar datas
        self.date_patterns = [
            r'(?:no dia|dia|na data|em|data)\s+(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)',
            r'(?:no dia|dia|na data|em|data)\s+(\d{1,2}\s+de\s+[a-zÀ-ú]+(?:\s+de\s+\d{2,4})?)',
            r'(?:em|para o|no mês de|mês de)\s+([a-zÀ-ú]+)(?:\s+de\s+(\d{2,4}))?',
            r'(?:próxima |proximo |proxima |próximo )(semana|mes|mês|segunda|terça|quarta|quinta|sexta|sábado|sabado|domingo)'
        ]
        
        # Padrões para identificar número de adultos
        self.adults_patterns = [
            r'(\d+)\s+(?:adultos?|passageiros?|pessoas?)',
            r'(?:para|com)\s+(\d+)\s+(?:adultos?|passageiros?|pessoas?)',
            r'(?:somos|seremos)\s+(\d+)\s+(?:adultos?|passageiros?|pessoas?)'
        ]
        
        # Palavras-chave que indicam uma intenção de busca de voos
        self.flight_search_keywords = [
            'voo', 'voos', 'passagem', 'passagens', 'bilhete', 'bilhetes',
            'avião', 'aviao', 'aéreo', 'aereo', 'aérea', 'aerea',
            'viagem', 'viagens', 'voar', 'buscar voo', 'buscar passagem'
        ]
    
    def is_flight_search_intent(self, message):
        """
        Verifica se a mensagem contém a intenção de buscar voos
        
        Args:
            message (str): Mensagem do usuário
            
        Returns:
            bool: True se a mensagem indica intenção de busca de voos
        """
        message = message.lower()
        
        # Verifica palavras-chave
        for keyword in self.flight_search_keywords:
            if keyword in message:
                return True
        
        # Verifica padrões de origem e destino
        for pattern in self.origin_patterns + self.destination_patterns:
            if re.search(pattern, message):
                return True
                
        return False
    
    def extract_flight_info(self, message, context=None):
        """
        Extrai informações de voo da mensagem do usuário
        
        Args:
            message (str): Mensagem do usuário
            context (dict, optional): Contexto anterior da conversa
            
        Returns:
            dict: Dicionário com informações extraídas (origin, destination, etc.)
                  ou None se não encontrar informações suficientes
        """
        message = message.lower()
        context = context or {}
        prior_info = context.get('travel_info', {})
        
        # Inicializar resultados com valores do contexto anterior, se existirem
        result = {
            'origin': prior_info.get('origin'),
            'destination': prior_info.get('destination'),
            'departure_date': prior_info.get('departure_date'),
            'return_date': prior_info.get('return_date'),
            'adults': prior_info.get('adults', 1)
        }
        
        # Verificar se há intenção de busca de voos
        if not self.is_flight_search_intent(message):
            return None
        
        # Extrair origem
        origin = None
        for pattern in self.origin_patterns:
            match = re.search(pattern, message)
            if match:
                origin_city = match.group(1).strip().lower()
                if origin_city in self.city_to_iata:
                    origin = self.city_to_iata[origin_city]
                    break
        
        # Extrair destino
        destination = None
        for pattern in self.destination_patterns:
            match = re.search(pattern, message)
            if match:
                dest_city = match.group(1).strip().lower()
                if dest_city in self.city_to_iata:
                    destination = self.city_to_iata[dest_city]
                    break
        
        # Extrair data de ida
        departure_date = None
        current_year = datetime.now().year
        for pattern in self.date_patterns:
            match = re.search(pattern, message)
            if match:
                date_str = match.group(1)
                
                # Processar datas no formato DD/MM ou DD/MM/YYYY
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts) == 2:
                        day, month = parts
                        date = f"{current_year}-{month.zfill(2)}-{day.zfill(2)}"
                        departure_date = date
                    elif len(parts) == 3:
                        day, month, year = parts
                        if len(year) == 2:
                            year = f"20{year}"
                        date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        departure_date = date
                
                # Processar datas no formato "próxima semana", "próximo mês", etc.
                elif 'próxima' in date_str or 'proxima' in date_str or 'proximo' in date_str or 'próximo' in date_str:
                    today = datetime.now()
                    if 'semana' in date_str:
                        future_date = today + timedelta(days=7)
                    elif 'mes' in date_str or 'mês' in date_str:
                        future_date = today + timedelta(days=30)
                    elif 'segunda' in date_str:
                        days_ahead = 0 - today.weekday() + 7
                        future_date = today + timedelta(days=days_ahead)
                    elif 'terça' in date_str:
                        days_ahead = 1 - today.weekday() + 7
                        future_date = today + timedelta(days=days_ahead)
                    elif 'quarta' in date_str:
                        days_ahead = 2 - today.weekday() + 7
                        future_date = today + timedelta(days=days_ahead)
                    elif 'quinta' in date_str:
                        days_ahead = 3 - today.weekday() + 7
                        future_date = today + timedelta(days=days_ahead)
                    elif 'sexta' in date_str:
                        days_ahead = 4 - today.weekday() + 7
                        future_date = today + timedelta(days=days_ahead)
                    elif 'sábado' in date_str or 'sabado' in date_str:
                        days_ahead = 5 - today.weekday() + 7
                        future_date = today + timedelta(days=days_ahead)
                    elif 'domingo' in date_str:
                        days_ahead = 6 - today.weekday() + 7
                        future_date = today + timedelta(days=days_ahead)
                    else:
                        future_date = today + timedelta(days=7)
                    
                    departure_date = future_date.strftime('%Y-%m-%d')
                
                # Se não conseguiu extrair data, mas identificou padrão, usar data futura padrão
                if not departure_date:
                    future_date = datetime.now() + timedelta(days=30)
                    departure_date = future_date.strftime('%Y-%m-%d')
                
                break
        
        # Se não extraiu data de nenhuma maneira, usar data padrão (30 dias no futuro)
        if not departure_date:
            future_date = datetime.now() + timedelta(days=30)
            departure_date = future_date.strftime('%Y-%m-%d')
        
        # Extrair número de adultos
        adults = 1  # valor padrão
        for pattern in self.adults_patterns:
            match = re.search(pattern, message)
            if match:
                try:
                    adults = int(match.group(1))
                    if adults <= 0:
                        adults = 1
                    elif adults > 9:
                        adults = 9  # máximo típico permitido pelas companhias
                except ValueError:
                    pass
                break
        
        # Atualizar o resultado com os valores extraídos
        if origin:
            result['origin'] = origin
        if destination:
            result['destination'] = destination
        if departure_date:
            result['departure_date'] = departure_date
        if adults != 1:  # só atualizar se diferente do padrão
            result['adults'] = adults
        
        # Verificar se temos informações suficientes para uma busca
        if result['origin'] and result['destination'] and result['departure_date']:
            # Marcar como "pronto para busca"
            result['ready_for_search'] = True
            return result
        else:
            # Identificamos intenção, mas faltam dados
            result['ready_for_search'] = False
            return result
        
        return None