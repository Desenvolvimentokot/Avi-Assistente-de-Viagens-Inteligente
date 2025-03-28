#!/usr/bin/env python3
"""
Processador de mensagens de chat para o Flai
Organiza informações do usuário para pesquisa de voos
"""
import re
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ChatProcessor:
    """
    Processa mensagens do chat para extrair informações de viagem
    """
    
    def __init__(self):
        self.MONTHS = {
            'janeiro': 1, 'jan': 1, 'fevereiro': 2, 'fev': 2, 'março': 3, 'mar': 3,
            'abril': 4, 'abr': 4, 'maio': 5, 'mai': 5, 'junho': 6, 'jun': 6,
            'julho': 7, 'jul': 7, 'agosto': 8, 'ago': 8, 'setembro': 9, 'set': 9,
            'outubro': 10, 'out': 10, 'novembro': 11, 'nov': 11, 'dezembro': 12, 'dez': 12
        }
        
        # Aeroportos comuns no Brasil (para validação)
        self.COMMON_AIRPORTS = {
            'GRU': {'code': 'GRU', 'name': 'Guarulhos', 'city': 'São Paulo'},
            'CGH': {'code': 'CGH', 'name': 'Congonhas', 'city': 'São Paulo'},
            'SDU': {'code': 'SDU', 'name': 'Santos Dumont', 'city': 'Rio de Janeiro'},
            'GIG': {'code': 'GIG', 'name': 'Galeão', 'city': 'Rio de Janeiro'},
            'BSB': {'code': 'BSB', 'name': 'Brasília', 'city': 'Brasília'},
            'CNF': {'code': 'CNF', 'name': 'Confins', 'city': 'Belo Horizonte'},
            'SSA': {'code': 'SSA', 'name': 'Salvador', 'city': 'Salvador'},
            'REC': {'code': 'REC', 'name': 'Recife', 'city': 'Recife'},
            'FOR': {'code': 'FOR', 'name': 'Fortaleza', 'city': 'Fortaleza'},
            'CWB': {'code': 'CWB', 'name': 'Curitiba', 'city': 'Curitiba'},
            'POA': {'code': 'POA', 'name': 'Porto Alegre', 'city': 'Porto Alegre'},
            'VCP': {'code': 'VCP', 'name': 'Viracopos', 'city': 'Campinas'},
            
            # Destinos internacionais populares
            'MIA': {'code': 'MIA', 'name': 'Miami', 'city': 'Miami'},
            'JFK': {'code': 'JFK', 'name': 'JFK', 'city': 'Nova York'},
            'EWR': {'code': 'EWR', 'name': 'Newark', 'city': 'Nova York'},
            'LHR': {'code': 'LHR', 'name': 'Heathrow', 'city': 'Londres'},
            'CDG': {'code': 'CDG', 'name': 'Charles de Gaulle', 'city': 'Paris'},
            'FCO': {'code': 'FCO', 'name': 'Fiumicino', 'city': 'Roma'},
            'BCN': {'code': 'BCN', 'name': 'El Prat', 'city': 'Barcelona'},
            'MAD': {'code': 'MAD', 'name': 'Barajas', 'city': 'Madri'},
            'LIS': {'code': 'LIS', 'name': 'Lisboa', 'city': 'Lisboa'},
            'SCL': {'code': 'SCL', 'name': 'Santiago', 'city': 'Santiago'},
            'EZE': {'code': 'EZE', 'name': 'Ezeiza', 'city': 'Buenos Aires'},
            'MEX': {'code': 'MEX', 'name': 'Cidade do México', 'city': 'Cidade do México'},
        }
        
        # Cidade para código IATA
        self.CITY_TO_AIRPORT = {
            'são paulo': ['GRU', 'CGH'],
            'rio de janeiro': ['GIG', 'SDU'],
            'rio': ['GIG', 'SDU'],
            'brasília': ['BSB'],
            'brasilia': ['BSB'],
            'belo horizonte': ['CNF'],
            'salvador': ['SSA'],
            'recife': ['REC'],
            'fortaleza': ['FOR'],
            'curitiba': ['CWB'],
            'porto alegre': ['POA'],
            'campinas': ['VCP'],
            
            'miami': ['MIA'],
            'nova york': ['JFK', 'EWR'],
            'new york': ['JFK', 'EWR'],
            'londres': ['LHR'],
            'london': ['LHR'],
            'paris': ['CDG'],
            'roma': ['FCO'],
            'rome': ['FCO'],
            'barcelona': ['BCN'],
            'madri': ['MAD'],
            'madrid': ['MAD'],
            'lisboa': ['LIS'],
            'lisbon': ['LIS'],
            'santiago': ['SCL'],
            'buenos aires': ['EZE'],
            'cidade do méxico': ['MEX'],
            'mexico city': ['MEX'],
        }
    
    def extract_travel_info(self, message, current_context=None):
        """
        Extrai informações de viagem de uma mensagem de texto
        Retorna um dicionário com as informações encontradas
        """
        if not current_context:
            current_context = {}
        
        # Extrair informações
        travel_info = self._extract_locations(message, current_context)
        travel_info.update(self._extract_dates(message, current_context))
        travel_info.update(self._extract_passengers(message, current_context))
        travel_info.update(self._extract_class(message, current_context))
        
        # Marcar como não confirmado
        travel_info['confirmed'] = False
        
        return travel_info
    
    def validate_travel_info(self, travel_info):
        """
        Valida as informações de viagem extraídas
        Retorna um dicionário com mensagens de erro, se houver
        """
        errors = {}
        
        # Verificar origem e destino
        if not travel_info.get('origin'):
            errors['origin'] = "Precisamos saber de onde você vai partir. Pode me informar a cidade ou aeroporto de origem?"
        
        if not travel_info.get('destination'):
            errors['destination'] = "Qual é o seu destino? Por favor, me informe para onde você quer ir."
        
        # Verificar datas
        if not travel_info.get('departure_date'):
            errors['departure_date'] = "Quando você planeja viajar? Preciso da data de partida."
        
        # Verificar se as datas estão no futuro
        if travel_info.get('departure_date'):
            try:
                departure_date = datetime.strptime(travel_info['departure_date'], '%Y-%m-%d')
                today = datetime.now()
                if departure_date < today:
                    errors['departure_date'] = "A data de partida precisa ser no futuro."
            except Exception:
                errors['departure_date'] = "Não consegui entender a data de partida. Por favor, informe no formato DD/MM/YYYY."
        
        return errors
    
    def format_travel_info_summary(self, travel_info):
        """
        Formata um resumo das informações de viagem para confirmar com o usuário
        """
        # Processar origem
        origin = travel_info.get('origin', 'não informado')
        if origin in self.COMMON_AIRPORTS:
            origin_display = f"{self.COMMON_AIRPORTS[origin]['city']} ({origin})"
        else:
            origin_display = origin
        
        # Processar destino
        destination = travel_info.get('destination', 'não informado')
        if destination in self.COMMON_AIRPORTS:
            destination_display = f"{self.COMMON_AIRPORTS[destination]['city']} ({destination})"
        else:
            destination_display = destination
        
        # Processar datas
        departure_date = "não informada"
        return_date = "não informada"
        
        if travel_info.get('departure_date'):
            try:
                date_obj = datetime.strptime(travel_info['departure_date'], '%Y-%m-%d')
                departure_date = date_obj.strftime('%d/%m/%Y')
            except Exception:
                departure_date = travel_info['departure_date']
        
        if travel_info.get('return_date'):
            try:
                date_obj = datetime.strptime(travel_info['return_date'], '%Y-%m-%d')
                return_date = date_obj.strftime('%d/%m/%Y')
            except Exception:
                return_date = travel_info['return_date']
        elif travel_info.get('date_range_end'):
            try:
                date_obj = datetime.strptime(travel_info['date_range_end'], '%Y-%m-%d')
                return_date = date_obj.strftime('%d/%m/%Y')
            except Exception:
                return_date = travel_info['date_range_end']
        
        # Processar passageiros
        adults = travel_info.get('adults', 1)
        children = travel_info.get('children', 0)
        infants = travel_info.get('infants', 0)
        
        passengers = f"{adults} adulto(s)"
        if children > 0:
            passengers += f", {children} criança(s)"
        if infants > 0:
            passengers += f", {infants} bebê(s)"
        
        # Processar classe
        travel_class = travel_info.get('class', 'ECONOMY')
        class_map = {
            'ECONOMY': 'Econômica',
            'PREMIUM_ECONOMY': 'Econômica Premium',
            'BUSINESS': 'Executiva',
            'FIRST': 'Primeira Classe'
        }
        class_display = class_map.get(travel_class, travel_class)
        
        # Montar resumo
        summary = [
            "**Resumo da sua solicitação de viagem:**",
            f"**Origem:** {origin_display}",
            f"**Destino:** {destination_display}",
            f"**Data de ida:** {departure_date}",
            f"**Data de volta:** {return_date}",
            f"**Passageiros:** {passengers}",
            f"**Classe:** {class_display}"
        ]
        
        return "\n".join(summary)
    
    def _extract_locations(self, message, current_context):
        """
        Extrai informações de origem e destino da mensagem
        """
        info = {}
        
        # Manter informações existentes
        if current_context.get('origin'):
            info['origin'] = current_context['origin']
        
        if current_context.get('destination'):
            info['destination'] = current_context['destination']
        
        # Padronizar mensagem
        message = message.lower()
        
        # Verificar padrões comuns para origem e destino
        origin_patterns = [
            r'(?:de|da|do|saindo de|partindo de|origem(?:\s+em)?) ([a-zA-Z\sáàâãéèêíìóòôõúùçñ]+?)(?:\s+(?:para|a|e|até|-)|\s*$)',
            r'(?:origem|partida|saída)(?:\s+em|\s+de|\s+do|\s+da|\s*:)?\s+([a-zA-Z\sáàâãéèêíìóòôõúùçñ]+?)(?:\s+(?:para|a|e|até|-)|\s*$)',
            r'viaj(?:ar|o|ando|arei)(?:\s+de|\s+do|\s+da)? ([a-zA-Z\sáàâãéèêíìóòôõúùçñ]+?)(?:\s+(?:para|a|até|e|-)|\s*$)',
            r'sa(?:ir|io|irei)(?:\s+de|\s+do|\s+da)? ([a-zA-Z\sáàâãéèêíìóòôõúùçñ]+?)(?:\s+(?:para|a|até|e|-)|\s*$)'
        ]
        
        dest_patterns = [
            r'(?:para|a|até|destino(?:\s+em)?|chegada(?:\s+em)?) ([a-zA-Z\sáàâãéèêíìóòôõúùçñ]+?)(?:\.|\s+(?:em|no dia|na data|dia|data)|\s*$)',
            r'(?:destino|chegada)(?:\s+em|\s+a|\s*:)?\s+([a-zA-Z\sáàâãéèêíìóòôõúùçñ]+?)(?:\.|\s+(?:em|no dia|na data|dia|data)|\s*$)',
            r'(?:ir|vou|irei|viajar)(?:\s+para|\s+a|\s+até)? ([a-zA-Z\sáàâãéèêíìóòôõúùçñ]+?)(?:\.|\s+(?:em|no dia|na data|dia|data)|\s*$)',
            r'(?:cheg(?:ar|o|arei)|ir)(?:\s+em|\s+a)? ([a-zA-Z\sáàâãéèêíìóòôõúùçñ]+?)(?:\.|\s+(?:em|no dia|na data|dia|data)|\s*$)'
        ]
        
        # Buscar códigos IATA na mensagem (3 letras maiúsculas)
        iata_codes = re.findall(r'\b([A-Z]{3})\b', message.upper())
        
        # Verificar códigos IATA encontrados
        for code in iata_codes:
            if code in self.COMMON_AIRPORTS:
                # Se for o primeiro código, assumir origem
                if not info.get('origin'):
                    info['origin'] = code
                # Se for o segundo código, assumir destino
                elif not info.get('destination') and code != info.get('origin'):
                    info['destination'] = code
        
        # Extrair origem usando padrões
        if not info.get('origin'):
            for pattern in origin_patterns:
                matches = re.search(pattern, message)
                if matches:
                    origin_text = matches.group(1).strip()
                    # Remover palavras genéricas como "cidade"
                    origin_text = re.sub(r'\b(?:cidade|aeroporto)\s+(?:de|do|da)?\s*', '', origin_text).strip()
                    
                    # Verificar se é um nome de cidade conhecido
                    origin_code = self._get_airport_code(origin_text)
                    if origin_code:
                        info['origin'] = origin_code
                        break
        
        # Extrair destino usando padrões
        if not info.get('destination'):
            for pattern in dest_patterns:
                matches = re.search(pattern, message)
                if matches:
                    dest_text = matches.group(1).strip()
                    # Remover palavras genéricas
                    dest_text = re.sub(r'\b(?:cidade|aeroporto)\s+(?:de|do|da)?\s*', '', dest_text).strip()
                    
                    # Verificar se é um nome de cidade conhecido
                    dest_code = self._get_airport_code(dest_text)
                    if dest_code:
                        info['destination'] = dest_code
                        break
        
        return info
    
    def _extract_dates(self, message, current_context):
        """
        Extrai informações de datas da mensagem
        """
        info = {}
        
        # Manter informações existentes
        if current_context.get('departure_date'):
            info['departure_date'] = current_context['departure_date']
        
        if current_context.get('return_date'):
            info['return_date'] = current_context['return_date']
        
        if current_context.get('date_range_start'):
            info['date_range_start'] = current_context['date_range_start']
        
        if current_context.get('date_range_end'):
            info['date_range_end'] = current_context['date_range_end']
        
        # Padronizar mensagem
        message = message.lower()
        
        # Buscar datas no formato DD/MM/YYYY
        date_matches = re.findall(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', message)
        
        # Processar datas encontradas
        for match in date_matches:
            day, month, year = match
            
            # Converter para inteiros
            day = int(day)
            month = int(month)
            
            # Processar ano (se fornecido)
            if year:
                year = int(year)
                # Ajustar anos de 2 dígitos
                if year < 100:
                    current_year = datetime.now().year
                    century = current_year // 100
                    year = century * 100 + year
            else:
                # Se não fornecido, usar ano atual ou próximo
                current_year = datetime.now().year
                date_with_current_year = datetime(current_year, month, day)
                
                # Se a data já passou este ano, assumir próximo ano
                if date_with_current_year < datetime.now():
                    year = current_year + 1
                else:
                    year = current_year
            
            # Validar data
            try:
                date_obj = datetime(year, month, day)
                date_str = date_obj.strftime('%Y-%m-%d')
                
                # Determinar se é data de ida ou volta
                if not info.get('departure_date'):
                    info['departure_date'] = date_str
                elif not info.get('return_date') and date_obj > datetime.strptime(info['departure_date'], '%Y-%m-%d'):
                    info['return_date'] = date_str
            except ValueError:
                # Data inválida
                continue
        
        # Buscar datas no formato "DD de mês de YYYY"
        date_text_pattern = r'(\d{1,2})\s+de\s+([a-záàâãéèêíìóòôõúùç]+)(?:\s+de\s+(\d{2,4}))?'
        date_text_matches = re.findall(date_text_pattern, message)
        
        # Processar datas textuais
        for match in date_text_matches:
            day, month_text, year = match
            
            # Converter para inteiros
            day = int(day)
            
            # Processar mês
            month_text = month_text.lower()
            if month_text in self.MONTHS:
                month = self.MONTHS[month_text]
            else:
                continue
            
            # Processar ano
            if year:
                year = int(year)
                # Ajustar anos de 2 dígitos
                if year < 100:
                    current_year = datetime.now().year
                    century = current_year // 100
                    year = century * 100 + year
            else:
                # Se não fornecido, usar ano atual ou próximo
                current_year = datetime.now().year
                date_with_current_year = datetime(current_year, month, day)
                
                # Se a data já passou este ano, assumir próximo ano
                if date_with_current_year < datetime.now():
                    year = current_year + 1
                else:
                    year = current_year
            
            # Validar data
            try:
                date_obj = datetime(year, month, day)
                date_str = date_obj.strftime('%Y-%m-%d')
                
                # Determinar se é data de ida ou volta
                if not info.get('departure_date'):
                    info['departure_date'] = date_str
                elif not info.get('return_date') and date_obj > datetime.strptime(info['departure_date'], '%Y-%m-%d'):
                    info['return_date'] = date_str
            except ValueError:
                # Data inválida
                continue
        
        # Buscar períodos (mês ou estação)
        month_patterns = [
            r'(?:em|no mês de|durante) ([a-záàâãéèêíìóòôõúùç]+)(?: de (\d{4}))?',
            r'([a-záàâãéèêíìóòôõúùç]+) (?:de|do ano de) (\d{4})'
        ]
        
        for pattern in month_patterns:
            matches = re.findall(pattern, message)
            for match in matches:
                if isinstance(match, tuple):
                    month_text = match[0].lower()
                    year_text = match[1] if len(match) > 1 and match[1] else None
                else:
                    continue
                
                # Verificar se é um mês válido
                if month_text in self.MONTHS:
                    month = self.MONTHS[month_text]
                    
                    # Determinar o ano
                    year = int(year_text) if year_text else datetime.now().year
                    
                    # Criar período de um mês
                    start_date = datetime(year, month, 1)
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
                    
                    # Adicionar ao resultado
                    info['date_range_start'] = start_date.strftime('%Y-%m-%d')
                    info['date_range_end'] = end_date.strftime('%Y-%m-%d')
        
        # Extrair períodos como "próxima semana", "próximo mês", etc.
        period_patterns = {
            r'próxima semana': (7, 14),
            r'próximo mês': (30, 60),
            r'próximos (\d+) dias': lambda x: (int(x), int(x) + 7),
            r'próximas (\d+) semanas': lambda x: (int(x) * 7, int(x) * 7 + 7),
            r'próximos (\d+) meses': lambda x: (int(x) * 30, int(x) * 30 + 30)
        }
        
        for pattern, days_func in period_patterns.items():
            matches = re.search(pattern, message)
            if matches:
                if callable(days_func):
                    value = matches.group(1)
                    start_days, end_days = days_func(value)
                else:
                    start_days, end_days = days_func
                
                today = datetime.now()
                start_date = today + timedelta(days=start_days)
                end_date = today + timedelta(days=end_days)
                
                info['date_range_start'] = start_date.strftime('%Y-%m-%d')
                info['date_range_end'] = end_date.strftime('%Y-%m-%d')
        
        # Se definido apenas um intervalo de datas, usar o início como data de partida
        if not info.get('departure_date') and info.get('date_range_start'):
            info['departure_date'] = info['date_range_start']
        
        return info
    
    def _extract_passengers(self, message, current_context):
        """
        Extrai informações de passageiros da mensagem
        """
        info = {}
        
        # Manter informações existentes
        if current_context.get('adults'):
            info['adults'] = current_context['adults']
        else:
            info['adults'] = 1  # Padrão
        
        if current_context.get('children'):
            info['children'] = current_context['children']
        else:
            info['children'] = 0  # Padrão
        
        if current_context.get('infants'):
            info['infants'] = current_context['infants']
        else:
            info['infants'] = 0  # Padrão
        
        # Padronizar mensagem
        message = message.lower()
        
        # Buscar números de adultos
        adult_patterns = [
            r'(\d+)[\s]*(?:adulto|pessoa|passageiro)s?',
            r'(?:adulto|pessoa|passageiro)s?[\s]*:[\s]*(\d+)',
            r'(?:para|com|somos)[\s]+(\d+)[\s]+(?:adulto|pessoa|passageiro)s?'
        ]
        
        for pattern in adult_patterns:
            matches = re.search(pattern, message)
            if matches:
                adults = int(matches.group(1))
                if adults > 0:
                    info['adults'] = adults
                    break
        
        # Buscar números de crianças
        child_patterns = [
            r'(\d+)[\s]*criança',
            r'criança[s]?[\s]*:[\s]*(\d+)',
            r'(?:com|e)[\s]+(\d+)[\s]+criança'
        ]
        
        for pattern in child_patterns:
            matches = re.search(pattern, message)
            if matches:
                children = int(matches.group(1))
                if children >= 0:
                    info['children'] = children
                    break
        
        # Buscar números de bebês
        infant_patterns = [
            r'(\d+)[\s]*(?:bebê|bebe|bebé)',
            r'(?:bebê|bebe|bebé)[s]?[\s]*:[\s]*(\d+)',
            r'(?:com|e)[\s]+(\d+)[\s]+(?:bebê|bebe|bebé)'
        ]
        
        for pattern in infant_patterns:
            matches = re.search(pattern, message)
            if matches:
                infants = int(matches.group(1))
                if infants >= 0:
                    info['infants'] = infants
                    break
        
        return info
    
    def _extract_class(self, message, current_context):
        """
        Extrai informações de classe da mensagem
        """
        info = {}
        
        # Manter informações existentes
        if current_context.get('class'):
            info['class'] = current_context['class']
        else:
            info['class'] = 'ECONOMY'  # Padrão
        
        # Padronizar mensagem
        message = message.lower()
        
        # Mapear termos para classes
        class_map = {
            'ECONOMY': ['econômica', 'economica', 'economia', 'classe econômica', 'classe economica', 'standard'],
            'PREMIUM_ECONOMY': ['premium economy', 'econômica premium', 'economica premium', 'premium', 'classe econômica premium'],
            'BUSINESS': ['executiva', 'business', 'classe executiva', 'business class'],
            'FIRST': ['primeira classe', 'primeira', 'first class', 'first']
        }
        
        # Buscar menções de classes
        for cls, terms in class_map.items():
            for term in terms:
                if term in message:
                    info['class'] = cls
                    return info
        
        return info
    
    def _get_airport_code(self, city_name):
        """
        Converte um nome de cidade para código IATA
        Retorna None se não encontrar correspondência
        """
        # Limpar o nome da cidade
        city_name = city_name.lower().strip()
        
        # Verificar se é um código IATA válido
        city_name_upper = city_name.upper()
        if len(city_name) == 3 and city_name_upper in self.COMMON_AIRPORTS:
            return city_name_upper
        
        # Verificar se é um nome de cidade conhecido
        if city_name in self.CITY_TO_AIRPORT:
            # Retornar o primeiro código associado à cidade
            return self.CITY_TO_AIRPORT[city_name][0]
        
        # Verificar correspondências parciais
        for known_city, codes in self.CITY_TO_AIRPORT.items():
            if city_name in known_city or known_city in city_name:
                return codes[0]
        
        # Não encontrou
        return None