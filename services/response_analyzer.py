"""
Analisador de respostas da AVI para extração de informações estruturadas
"""

import re
import logging
from datetime import datetime, timedelta

# Configurar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseAnalyzer:
    """
    Classe responsável por analisar as respostas da AVI e extrair 
    informações estruturadas para uso no sistema.
    """
    
    @staticmethod
    def extract_travel_info_from_response(response_text):
        """
        Extrai informações de viagem quando a AVI responde com um formato específico.
        Procura por blocos demarcados [DADOS_VIAGEM] na resposta.
        
        Args:
            response_text: Texto da resposta da AVI
            
        Returns:
            dict: Informações extraídas sobre a viagem ou None se não encontrar
        """
        # Verificar se temos o marcador de dados de viagem na resposta
        if '[DADOS_VIAGEM]' not in response_text or '[/DADOS_VIAGEM]' not in response_text:
            logger.debug("Marcadores [DADOS_VIAGEM] não encontrados na resposta")
            return None
            
        try:
            # Extrair o bloco de dados
            pattern = r'\[DADOS_VIAGEM\](.*?)\[/DADOS_VIAGEM\]'
            match = re.search(pattern, response_text, re.DOTALL)
            
            if not match:
                logger.warning("Não foi possível extrair o bloco de dados de viagem com regex")
                return None
                
            data_block = match.group(1).strip()
            logger.debug(f"Bloco de dados extraído: {data_block}")
            
            # Inicializar dicionário de informações
            travel_info = {}
            
            # Processar linha por linha
            for line in data_block.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Extrair chave e valor
                parts = line.split(':', 1)
                if len(parts) != 2:
                    continue
                    
                key = parts[0].strip().lower()
                value = parts[1].strip()
                
                # Mapear chaves do formato apresentado para o formato interno
                key_mapping = {
                    'origem': 'origin',
                    'destino': 'destination',
                    'data_ida': 'departure_date',
                    'data de ida': 'departure_date',
                    'data_volta': 'return_date',
                    'data de volta': 'return_date',
                    'passageiros': 'adults',
                    'tipo_viagem': 'trip_type'
                }
                
                internal_key = key_mapping.get(key.lower(), key.lower())
                
                # Processar valores específicos
                if internal_key == 'origin' or internal_key == 'destination':
                    # Extrair código IATA entre parênteses (ex: "São Paulo (GRU)" -> "GRU")
                    iata_match = re.search(r'\(([A-Z]{3})\)', value)
                    if iata_match:
                        value = iata_match.group(1)
                elif internal_key == 'departure_date' or internal_key == 'return_date':
                    # Converter para formato YYYY-MM-DD se não estiver
                    if not re.match(r'\d{4}-\d{2}-\d{2}', value):
                        try:
                            # Tentar vários formatos comuns
                            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']:
                                try:
                                    date_obj = datetime.strptime(value, fmt)
                                    value = date_obj.strftime('%Y-%m-%d')
                                    break
                                except ValueError:
                                    continue
                        except Exception as e:
                            logger.warning(f"Não foi possível converter data '{value}': {str(e)}")
                elif internal_key == 'adults':
                    # Extrair apenas o número de adultos
                    adults_match = re.search(r'(\d+)', value)
                    if adults_match:
                        value = int(adults_match.group(1))
                elif internal_key == 'trip_type':
                    # Normalizar tipo de viagem
                    if 'ida_e_volta' in value.lower() or 'ida e volta' in value.lower():
                        value = 'round_trip'
                    elif 'somente_ida' in value.lower() or 'somente ida' in value.lower() or 'só ida' in value.lower():
                        value = 'one_way'
                
                # Adicionar ao dicionário de informações
                travel_info[internal_key] = value
            
            # Verificar se temos as informações mínimas necessárias
            required_fields = ['origin', 'destination', 'departure_date']
            for field in required_fields:
                if field not in travel_info:
                    logger.warning(f"Campo obrigatório '{field}' não encontrado nos dados extraídos")
                    return None
            
            logger.info(f"Informações de viagem extraídas com sucesso: {travel_info}")
            return travel_info
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações de viagem da resposta: {str(e)}")
            return None