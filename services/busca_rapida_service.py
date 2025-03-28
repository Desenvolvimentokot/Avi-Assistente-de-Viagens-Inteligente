#!/usr/bin/env python3
"""
Serviço de busca rápida de voos baseado no SDK da Amadeus.
Este serviço integra o processador de chat com os serviços de API para realizar buscas.
"""
import logging
import json
from datetime import datetime, timedelta
from services.amadeus_sdk_service import AmadeusSDKService
from services.chat_processor import ChatProcessor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('busca_rapida_service')

class BuscaRapidaService:
    """
    Serviço que coordena o fluxo de busca rápida de voos
    """
    
    def __init__(self):
        """Inicializa o serviço com as dependências necessárias"""
        self.amadeus_service = AmadeusSDKService()
        self.chat_processor = ChatProcessor()
        self.max_dates_to_check = 3  # Máximo de datas para verificar nas buscas de melhor preço
    
    def process_message(self, message, context=None):
        """
        Processa uma mensagem do usuário e atualiza o contexto da conversa
        Retorna o contexto atualizado e uma resposta para o usuário
        """
        if not context:
            context = {
                'step': 0,  # Etapa atual do fluxo
                'travel_info': {},  # Informações de viagem extraídas
                'search_results': None,  # Resultados da busca
                'error': None  # Mensagens de erro
            }
        
        # Log da etapa atual
        logger.info(f"Etapa {context['step']}: {self._get_step_name(context['step'])}")
        
        # Processar com base na etapa atual
        if context['step'] == 0:
            return self._process_step_0(message, context)
        elif context['step'] == 1:
            return self._process_step_1(message, context)
        elif context['step'] == 2:
            return self._process_step_2(message, context)
        else:
            context['step'] = 0  # Reiniciar o fluxo
            return self._process_step_0(message, context)
    
    def _process_step_0(self, message, context):
        """
        Etapa 0: Extração inicial de informações
        """
        travel_info = self.chat_processor.extract_travel_info(message)
        
        # Atualizar contexto
        context['travel_info'].update(travel_info)
        
        # Validar informações
        errors = self.chat_processor.validate_travel_info(context['travel_info'])
        
        if errors:
            # Se houver erros, solicitar mais informações
            error_messages = list(errors.values())
            response = f"Preciso de algumas informações adicionais para buscar voos:\n\n" + "\n".join(error_messages)
            
            # Manter na mesma etapa
            return context, response
        else:
            # Se todas as informações necessárias estiverem presentes, avançar para a próxima etapa
            context['step'] = 1
            
            # Formatar resumo para confirmar com o usuário
            travel_summary = self.chat_processor.format_travel_info_summary(context['travel_info'])
            response = f"{travel_summary}\n\nEstas informações estão corretas? Posso realizar a busca?"
            
            return context, response
    
    def _process_step_1(self, message, context):
        """
        Etapa 1: Confirmação das informações
        """
        # Verificar se o usuário confirmou
        confirmation = self._check_confirmation(message)
        
        if confirmation is None:
            # Resposta ambígua, continuar solicitando confirmação
            response = "Por favor, confirme se posso realizar a busca com essas informações."
            return context, response
        
        if not confirmation:
            # Usuário não confirmou, voltar para a etapa 0
            context['step'] = 0
            response = "Entendi. Por favor, me forneça as informações corretas para sua viagem."
            return context, response
        
        # Usuário confirmou, marcar como confirmado e avançar para a próxima etapa
        context['travel_info']['confirmed'] = True
        context['step'] = 2
        
        # Realizar busca
        response = "Ótimo! Estou buscando as melhores opções para sua viagem. Um momento..."
        
        return context, response
    
    def _process_step_2(self, message, context):
        """
        Etapa 2: Busca e apresentação de resultados
        """
        logger.info("Etapa 2: Busca e apresentação de resultados")
        
        # Verificar se já temos informações suficientes
        if not context['travel_info'].get('confirmed'):
            # Se não confirmado, voltar para a etapa 1
            context['step'] = 1
            travel_summary = self.chat_processor.format_travel_info_summary(context['travel_info'])
            response = f"{travel_summary}\n\nEstas informações estão corretas? Posso realizar a busca?"
            return context, response
        
        # Se já temos resultados, processar a mensagem como uma solicitação adicional
        if context['search_results']:
            # Implementar lógica para responder a perguntas sobre os resultados
            # Por enquanto, apenas retornar os resultados novamente
            response = "Aqui estão as opções que encontrei para sua viagem:\n\n"
            response += self._format_search_results(context['search_results'])
            return context, response
        
        # Caso contrário, realizar a busca
        logger.info("Informações suficientes para busca encontradas")
        search_results = self._perform_search(context['travel_info'])
        
        # Armazenar resultados no contexto
        context['search_results'] = search_results
        
        # Formatar resposta com os resultados
        if 'error' in search_results:
            response = f"Desculpe, tive um problema ao buscar voos: {search_results['error']}"
        else:
            response = "Aqui estão as opções que encontrei para sua viagem:\n\n"
            response += self._format_search_results(search_results)
        
        return context, response
    
    def _perform_search(self, travel_info):
        """
        Realiza a busca de voos com base nas informações do usuário
        """
        try:
            # Determinar o tipo de busca (data específica ou período flexível)
            if travel_info.get('date_range_start') and travel_info.get('date_range_end'):
                logger.info(f"Buscando melhores preços para o período: {travel_info['date_range_start']} a {travel_info['date_range_end']}")
                return self._search_best_prices(travel_info)
            else:
                logger.info(f"Buscando voos para data específica: {travel_info['departure_date']}")
                return self._search_specific_date(travel_info)
        except Exception as e:
            logger.error(f"Erro na busca: {str(e)}")
            return {"error": "Ocorreu um erro durante a busca. Por favor, tente novamente mais tarde."}
    
    def _search_best_prices(self, travel_info):
        """
        Busca melhores preços em um período
        """
        # Preparar parâmetros de busca
        origin = travel_info.get('origin')
        destination = travel_info.get('destination')
        departure_date = travel_info.get('date_range_start') or travel_info.get('departure_date')
        return_date = travel_info.get('date_range_end') or travel_info.get('return_date')
        adults = travel_info.get('adults', 1)
        currency = 'BRL'
        
        logger.info(f"Buscando melhores preços para {origin} -> {destination}")
        
        # Inicializar serviços de API
        amadeus_service = self.amadeus_service
        logger.info("Serviços de API inicializados")
        
        # Parâmetros para busca de melhores preços
        search_params = {
            'origin': origin,
            'destination': destination, 
            'departure_date': departure_date,
            'return_date': return_date,
            'adults': adults,
            'currency': currency,
            'max_dates_to_check': self.max_dates_to_check
        }
        
        logger.info(f"Iniciando busca com parâmetros: {search_params}")
        
        # Buscar melhores preços
        try:
            # Buscar com Amadeus
            params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'returnDate': return_date,
                'adults': adults,
                'currencyCode': currency,
                'max_dates_to_check': self.max_dates_to_check
            }
            
            best_prices_results = amadeus_service.search_best_prices(params)
            
            # Verificar resultados
            if 'best_prices' in best_prices_results and best_prices_results['best_prices']:
                logger.info("Busca de melhores preços bem-sucedida")
                return best_prices_results
            elif 'error' in best_prices_results:
                logger.error(f"Erro na busca de melhores preços: {best_prices_results['error']}")
                return {"error": best_prices_results['error']}
            else:
                logger.warning("Sem resultados na busca de melhores preços")
                return {"error": "No momento não foi possível obter dados de preços para o período solicitado."}
            
        except Exception as e:
            logger.error(f"Erro na busca de melhores preços: {str(e)}")
            return {"error": "No momento não foi possível obter dados reais de preços. Por favor, tente novamente mais tarde."}
    
    def _search_specific_date(self, travel_info):
        """
        Busca voos para uma data específica
        """
        # Preparar parâmetros de busca
        origin = travel_info.get('origin')
        destination = travel_info.get('destination')
        departure_date = travel_info.get('departure_date')
        return_date = travel_info.get('return_date')
        adults = travel_info.get('adults', 1)
        travel_class = travel_info.get('class', 'ECONOMY')
        currency = 'BRL'
        
        logger.info(f"Buscando voos para {origin} -> {destination} em {departure_date}")
        
        # Inicializar serviço Amadeus
        amadeus_service = self.amadeus_service
        
        # Parâmetros para busca de voos
        params = {
            'originLocationCode': origin,
            'destinationLocationCode': destination,
            'departureDate': departure_date,
            'adults': adults,
            'currencyCode': currency,
            'max': 5  # Limitar o número de resultados
        }
        
        # Adicionar data de retorno se disponível
        if return_date:
            params['returnDate'] = return_date
        
        # Buscar voos
        try:
            flight_results = amadeus_service.search_flights(params)
            
            # Verificar resultados
            if 'data' in flight_results and flight_results['data']:
                logger.info(f"Busca de voos bem-sucedida: {len(flight_results['data'])} resultados")
                return {
                    "flights": flight_results['data'],
                    "dictionaries": flight_results.get('dictionaries'),
                    "meta": flight_results.get('meta')
                }
            elif 'error' in flight_results:
                logger.error(f"Erro na busca de voos: {flight_results['error']}")
                return {"error": flight_results['error']}
            else:
                logger.warning("Sem resultados na busca de voos")
                return {"error": "No momento não foi possível encontrar voos para a data solicitada."}
            
        except Exception as e:
            logger.error(f"Erro na busca de voos: {str(e)}")
            return {"error": "No momento não foi possível obter dados reais de voos. Por favor, tente novamente mais tarde."}
    
    def _format_search_results(self, search_results):
        """
        Formata os resultados da busca para apresentação ao usuário
        """
        # Verificar se temos resultados de melhores preços
        if 'best_prices' in search_results and search_results['best_prices']:
            return self._format_best_prices_results(search_results)
        
        # Verificar se temos resultados de voos
        if 'flights' in search_results and search_results['flights']:
            return self._format_flight_results(search_results)
        
        # Caso não tenha resultados
        return "Não foi possível encontrar opções que atendam aos seus critérios."
    
    def _format_best_prices_results(self, results):
        """
        Formata os resultados de melhores preços
        """
        if not results.get('best_prices'):
            return "Não foram encontrados preços para o período solicitado."
        
        # Obter informações
        origin = results.get('origin', '')
        destination = results.get('destination', '')
        currency = results.get('currency', 'BRL')
        best_prices = results.get('best_prices', [])
        
        # Ordenar por preço
        best_prices.sort(key=lambda x: x['price'])
        
        # Obter o mais barato e alguns outros bons preços
        cheapest = best_prices[0] if best_prices else None
        other_options = best_prices[1:4] if len(best_prices) > 1 else []
        
        # Formatar resposta
        response = []
        
        # Adicionar marcador para processamento front-end
        response.append(f'<div class="price-options" data-price-options=\'{json.dumps(best_prices)}\'>Processando opções de preço...</div>')
        
        # Se não tiver nenhuma opção
        if not cheapest:
            return "Não foram encontrados preços para o período solicitado."
        
        # Texto explicativo
        origin_name = cheapest.get('origin_info', {}).get('name', origin) if cheapest.get('origin_info') else origin
        dest_name = cheapest.get('destination_info', {}).get('name', destination) if cheapest.get('destination_info') else destination
        
        response.append(f"🔍 **Melhor preço encontrado para {origin_name} → {dest_name}**")
        
        # Formatar data
        cheapest_date = cheapest.get('date', '')
        try:
            date_obj = datetime.strptime(cheapest_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d/%m/%Y')
        except:
            formatted_date = cheapest_date
        
        # Detalhes do melhor preço
        response.append(f"📅 **Data:** {formatted_date}")
        response.append(f"💰 **Preço:** R$ {cheapest['price']:.2f}")
        
        # Adicionar link de compra se disponível
        if cheapest.get('purchaseLinks'):
            provider = cheapest['purchaseLinks'][0].get('provider', 'agência parceira')
            purchase_url = cheapest['purchaseLinks'][0].get('url', '')
            response.append(f"🔗 **Reservar em:** {provider}")
        
        # Outras opções
        if other_options:
            response.append("\n**Outras datas com bons preços:**")
            
            for i, option in enumerate(other_options):
                try:
                    date_obj = datetime.strptime(option.get('date', ''), '%Y-%m-%d')
                    option_date = date_obj.strftime('%d/%m/%Y')
                except:
                    option_date = option.get('date', '')
                
                price = option.get('price', 0)
                response.append(f"• {option_date}: R$ {price:.2f}")
        
        # Retornar resposta formatada
        return "\n".join(response)
    
    def _format_flight_results(self, results):
        """
        Formata os resultados de busca de voos
        """
        if not results.get('flights'):
            return "Não foram encontrados voos para a data solicitada."
        
        flights = results.get('flights', [])
        dictionaries = results.get('dictionaries', {})
        
        # Ordenar por preço
        flights.sort(key=lambda x: float(x['price']['total']))
        
        # Pegar apenas os 5 primeiros resultados
        flights = flights[:5]
        
        # Formatar resposta
        response = []
        
        # Adicionar marcador para processamento front-end
        response.append(f'<div class="flight-results" data-flights=\'{json.dumps(flights)}\'>Processando resultados de voos...</div>')
        
        # Textos explicativos
        if flights:
            first_flight = flights[0]
            
            # Extrair informações do primeiro voo
            price = float(first_flight['price']['total'])
            currency = first_flight['price']['currency']
            
            # Origem e destino
            origin = first_flight['itineraries'][0]['segments'][0]['departure']['iataCode']
            destination = first_flight['itineraries'][0]['segments'][-1]['arrival']['iataCode']
            
            # Data
            departure_date = first_flight['itineraries'][0]['segments'][0]['departure']['at']
            try:
                date_obj = datetime.strptime(departure_date.split('T')[0], '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d/%m/%Y')
            except:
                formatted_date = departure_date.split('T')[0]
            
            # Hora
            departure_time = departure_date.split('T')[1][:5]
            
            response.append(f"✈️ **Voo de {origin} para {destination} em {formatted_date}**")
            response.append(f"💰 **A partir de:** R$ {price:.2f}")
            response.append("\nEssas são as melhores opções que encontrei para sua viagem.")
        
        # Retornar resposta formatada
        return "\n".join(response)
    
    def _check_confirmation(self, message):
        """
        Verifica se o usuário confirmou ou negou
        Retorna: True (confirmou), False (negou) ou None (resposta ambígua)
        """
        # Normalizar mensagem
        text = message.lower()
        
        # Palavras e frases de confirmação
        positive_words = [
            'sim', 'yes', 'correto', 'certo', 'isso mesmo', 'exato', 'confirmo',
            'pode ser', 'está certo', 'está correto', 'confirmado', 'ok', 'okay', 
            'perfeito', 'está perfeito', 'pode buscar', 'busque', 'buscar', 'procure',
            'procurar', 'vamos lá', 'vá em frente', 'prosseguir', 'continuar'
        ]
        
        # Palavras e frases de negação
        negative_words = [
            'não', 'no', 'nao', 'incorreto', 'errado', 'não está certo', 'não correto',
            'não é isso', 'mudei de ideia', 'diferente', 'cancelar', 'não quero',
            'não desejo', 'reiniciar', 'começar de novo', 'mudar', 'alterar'
        ]
        
        # Verificar confirmação
        for word in positive_words:
            if word in text:
                return True
        
        # Verificar negação
        for word in negative_words:
            if word in text:
                return False
        
        # Resposta ambígua
        return None
    
    def _get_step_name(self, step):
        """Retorna o nome da etapa atual"""
        steps = {
            0: "Extração inicial de informações",
            1: "Confirmação das informações",
            2: "Busca e apresentação de resultados"
        }
        return steps.get(step, "Etapa desconhecida")