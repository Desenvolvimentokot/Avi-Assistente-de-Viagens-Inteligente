"""
Analisador de respostas da AVI para extração de informações estruturadas
"""

import re
import logging
from datetime import datetime, timedelta

# Configurar logger
logging.basicConfig(level=logging.DEBUG)  # Aumentar nível de log para DEBUG
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
        if not response_text:
            logger.error("❌ Texto da resposta vazio, impossível extrair informações")
            return None

        # Log para depuração
        logger.warning("🔍 ANALISANDO RESPOSTA EM BUSCA DE DADOS DE VIAGEM")
        logger.debug(f"Texto completo da resposta: {response_text[:200]}...")

        # Verificar se temos o marcador de dados de viagem na resposta
        if '[DADOS_VIAGEM]' not in response_text or '[/DADOS_VIAGEM]' not in response_text:
            logger.warning("❌ Marcadores [DADOS_VIAGEM] não encontrados na resposta")
            return None
        else:
            logger.warning("✅ Marcadores [DADOS_VIAGEM] encontrados na resposta!")

        try:
            # Extrair o bloco de dados
            pattern = r'\[DADOS_VIAGEM\](.*?)\[/DADOS_VIAGEM\]'
            match = re.search(pattern, response_text, re.DOTALL)

            if not match:
                logger.warning("❌ Não foi possível extrair o bloco de dados de viagem com regex")
                return None

            data_block = match.group(1).strip()
            logger.warning(f"✅ Bloco de dados extraído: {data_block}")

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
                    logger.warning(f"⚠️ Linha ignorada, formato inválido: {line}")
                    continue

                key = parts[0].strip().lower()
                value = parts[1].strip()

                logger.debug(f"Linha processada: '{key}': '{value}'")

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
                logger.debug(f"Chave mapeada: '{key}' -> '{internal_key}'")

                # Processar valores específicos
                if internal_key == 'origin' or internal_key == 'destination':
                    # Extrair código IATA entre parênteses (ex: "São Paulo (GRU)" -> "GRU")
                    iata_match = re.search(r'\(([A-Z]{3})\)', value)
                    if iata_match:
                        value = iata_match.group(1)
                        logger.debug(f"Código IATA extraído: {value}")
                    else:
                        logger.warning(f"⚠️ Código IATA não encontrado em '{value}'")
                elif internal_key == 'departure_date' or internal_key == 'return_date':
                    # Converter para formato YYYY-MM-DD se não estiver
                    original_value = value
                    if not re.match(r'\d{4}-\d{2}-\d{2}', value):
                        try:
                            # Tentar vários formatos comuns
                            converted = False
                            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']:
                                try:
                                    date_obj = datetime.strptime(value, fmt)
                                    value = date_obj.strftime('%Y-%m-%d')
                                    converted = True
                                    logger.debug(f"Data convertida: '{original_value}' -> '{value}'")
                                    break
                                except ValueError:
                                    continue
                            if not converted:
                                logger.warning(f"⚠️ Não foi possível converter a data: '{original_value}'")
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao converter data '{original_value}': {str(e)}")
                elif internal_key == 'adults':
                    # Extrair apenas o número de adultos
                    adults_match = re.search(r'(\d+)', value)
                    if adults_match:
                        try:
                            value = int(adults_match.group(1))
                            logger.debug(f"Número de adultos extraído: {value}")
                        except ValueError:
                            logger.warning(f"⚠️ Não foi possível converter número de adultos: '{value}'")
                    else:
                        logger.warning(f"⚠️ Número de adultos não encontrado em '{value}'")
                        # Valor padrão para evitar erros
                        value = 1
                elif internal_key == 'trip_type':
                    # Normalizar tipo de viagem
                    original_value = value
                    if 'ida_e_volta' in value.lower() or 'ida e volta' in value.lower():
                        value = 'round_trip'
                    elif 'somente_ida' in value.lower() or 'somente ida' in value.lower() or 'só ida' in value.lower():
                        value = 'one_way'
                    logger.debug(f"Tipo de viagem normalizado: '{original_value}' -> '{value}'")

                # Adicionar ao dicionário de informações
                travel_info[internal_key] = value
                logger.debug(f"Adicionado ao dicionário: {internal_key}={value}")

            # Verificar se temos as informações mínimas necessárias
            required_fields = ['origin', 'destination', 'departure_date']
            missing_fields = [field for field in required_fields if field not in travel_info]

            if missing_fields:
                logger.warning(f"❌ Campos obrigatórios ausentes: {missing_fields}")
                return None

            # Verificar e garantir que o campo 'adults' seja um número inteiro
            if 'adults' in travel_info:
                if not isinstance(travel_info['adults'], int):
                    try:
                        travel_info['adults'] = int(travel_info['adults'])
                    except (ValueError, TypeError):
                        logger.warning(f"⚠️ Convertendo valor inválido de 'adults' para o padrão: 1")
                        travel_info['adults'] = 1
            else:
                # Definir valor padrão para evitar erros
                travel_info['adults'] = 1
                logger.debug("Adicionado valor padrão para 'adults': 1")

            # Garantir que o valor de trip_type seja válido
            if 'trip_type' in travel_info:
                if travel_info['trip_type'] not in ['round_trip', 'one_way']:
                    # Se não for um valor válido, determinar pelo campo return_date
                    if 'return_date' in travel_info and travel_info['return_date']:
                        travel_info['trip_type'] = 'round_trip'
                    else:
                        travel_info['trip_type'] = 'one_way'
            else:
                # Determinar tipo de viagem pela presença de return_date
                if 'return_date' in travel_info and travel_info['return_date']:
                    travel_info['trip_type'] = 'round_trip'
                else:
                    travel_info['trip_type'] = 'one_way'
                logger.debug(f"Tipo de viagem determinado: {travel_info['trip_type']}")

            logger.warning(f"✅ SUCESSO! Informações de viagem extraídas: {travel_info}")

            # Adicionar flag para indicar que o redirecionamento deve acontecer
            travel_info['should_redirect'] = True

            return travel_info

        except Exception as e:
            import traceback
            logger.error(f"❌ Erro ao extrair informações de viagem: {str(e)}")
            logger.error(traceback.format_exc())
            return None