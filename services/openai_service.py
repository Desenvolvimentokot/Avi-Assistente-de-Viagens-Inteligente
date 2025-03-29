import os
import logging
import requests
import json
import inspect
import traceback

class OpenAIService:
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.api_url = 'https://api.openai.com/v1/chat/completions'
        self.model = 'gpt-4o'
        
    def create_chat_completion(self, messages, temperature=0.7, max_tokens=1000, model=None):
        """
        Cria uma resposta usando a API de chat do OpenAI
        
        Parâmetros:
        - messages: lista de mensagens no formato esperado pela API
        - temperature: controle de aleatoriedade (0.0 a 1.0)
        - max_tokens: número máximo de tokens na resposta
        - model: modelo específico a ser usado (se None, usa o padrão da classe)
        """
        if not self.api_key:
            logging.error("API key da OpenAI não configurada")
            return {'error': 'API key da OpenAI não configurada. Por favor, configure a chave nas variáveis de ambiente.'}
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # Usar o modelo especificado ou o padrão da classe
        use_model = model if model else self.model
        
        data = {
            'model': use_model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        # Preparar resposta de fallback para caso ocorra erro
        fallback_response = {'choices': [{'message': {'content': 'Estou tendo dificuldades para processar sua solicitação. Por favor, tente novamente em alguns instantes.'}}]}
        
        try:
            logging.info(f"[OPENAI SERVICE DEBUG] Enviando requisição para OpenAI API - Função: {str(inspect.currentframe().f_back.f_code.co_name)}")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30  # Adicionar timeout para evitar esperas indefinidas
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na chamada à API OpenAI: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Resposta da API: {e.response.text}")
                try:
                    error_json = e.response.json()
                    error_message = error_json.get('error', {}).get('message', str(e))
                    logging.error(f"Mensagem de erro da API: {error_message}")
                    return {'error': f'Erro na API OpenAI: {error_message}'}
                except:
                    pass
            return {'error': f'Erro de comunicação com a API OpenAI: {str(e)}'}
        except Exception as e:
            logging.error(f"Erro inesperado ao chamar a API OpenAI: {str(e)}")
            return {'error': f'Erro inesperado: {str(e)}'}
    
    # Função antiga removida para evitar duplicação
    
    def travel_assistant(self, user_message, conversation_history=None, system_context=""):
        """
        FUNÇÃO DESATIVADA PARA A PARTE DE BUSCA DE VOOS

        Este serviço foi substituído por um sistema de busca direta na API Amadeus
        para garantir que apenas dados reais sejam apresentados ao usuário.
        
        AVISO: Esta função faz a verificação de conteúdo e BLOQUEIA chamadas relacionadas 
        a voos ou ofertas de viagem, que devem passar exclusivamente pelo conector da Amadeus.
        """
        if conversation_history is None:
            conversation_history = []
        
        # VERIFICAÇÃO CRÍTICA: Detectar se é uma solicitação de busca de voos/passagens
        is_flight_search = False
        
        # Lista de palavras-chave para identificar buscas de voos
        flight_keywords = [
            "voo", "passagem", "voar", "aéreo", "aérea", "avião", "aereo", "aerea",
            "aeroporto", "partida", "chegada", "origem", "destino", "decolagem", "pouso",
            "companhia aérea", "companhia aerea", "GOL", "LATAM", "Azul", "ida e volta", "só ida",
            "confirmo", "quero essas", "confirmar", "reservar", "comprar passagem", "comprar voo"
        ]
        
        # Verificar se a mensagem contém alguma palavra-chave de busca de voos
        user_message_lower = user_message.lower()
        if any(keyword in user_message_lower for keyword in flight_keywords):
            is_flight_search = True
            
        # Verificar se o contexto indica busca de voos
        flight_context_keywords = [
            "busca de voos", "busca de passagens", "pesquisa de voos", "voos disponíveis",
            "passagens disponíveis", "confirmar detalhes", "busca confirmada"
        ]
        
        if system_context and any(keyword in system_context.lower() for keyword in flight_context_keywords):
            is_flight_search = True
        
        # SE FOR BUSCA DE VOOS, RETORNAR RESPOSTA PADRONIZADA SEM CHAMAR API
        if is_flight_search:
            # IMPORTANTE: Isso evita COMPLETAMENTE a chamada à API OpenAI para buscas de voos
            logging.warning(f"🚫 BLOQUEIO TOTAL: Solicitação de voos detectada. Usando fluxo da Amadeus em vez de OpenAI.")
            return {
                'response': "Estou buscando as melhores opções de voos usando a API da Amadeus..."
            }
        
        # PARA OUTROS TIPOS DE SOLICITAÇÕES, PODE CHAMAR A API NORMALMENTE
        logging.info(f"Processando mensagem de usuário não relacionada a voos (conversa geral)")
        
        # Importar os prompts do Avi
        from services.prompts.avi_system_prompt import AVI_SYSTEM_PROMPT
        from services.prompts.busca_rapida_prompt import BUSCA_RAPIDA_PROMPT
        from services.prompts.planejamento_completo_prompt import PLANEJAMENTO_COMPLETO_PROMPT
        
        # Identificar o contexto atual com base na mensagem e histórico
        current_prompt = AVI_SYSTEM_PROMPT
        
        # Verificar se há um contexto específico de modo de busca
        if "planejamento completo" in user_message.lower() or any("planejamento completo" in msg.get('content', '').lower() for msg in conversation_history if msg.get('is_user', False)):
            current_prompt += "\n\n" + PLANEJAMENTO_COMPLETO_PROMPT
            
        # Criação do sistema de mensagens com o contexto da Avi
        base_system_content = current_prompt
        
        # Adicionar contexto específico do sistema, se fornecido
        if system_context:
            base_system_content += f"\n\n{system_context}"
            
        # IMPORTANTE: Avisar explicitamente para NÃO simular voos
        base_system_content += """
        ATENÇÃO CRÍTICA: NÃO TENTE BUSCAR OU SIMULAR INFORMAÇÕES DE VOOS!
        
        - NUNCA forneça informações de preços, horários ou disponibilidade de voos
        - NUNCA simule ou invente informações de passagens aéreas
        - Se o usuário perguntar sobre voos específicos, explique que você está verificando
          a API da Amadeus para obter dados reais e confiáveis
        - Apenas responda perguntas gerais sobre viagens, sem fornecer informações de voos específicos
        """
            
        system_message = {
            "role": "system",
            "content": base_system_content
        }
        
        # Montagem do histórico de conversa no formato esperado pela API
        api_messages = [system_message]
        
        for msg in conversation_history:
            if msg.get('is_user'):
                api_messages.append({
                    "role": "user",
                    "content": msg.get('content', '')
                })
            else:
                api_messages.append({
                    "role": "assistant", 
                    "content": msg.get('content', '')
                })
        
        # Adição da mensagem atual do usuário
        api_messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Chamada à API
        response = self.create_chat_completion(api_messages)
        
        if 'error' in response:
            return response
        
        try:
            # Extração da resposta do assistente
            assistant_response = response['choices'][0]['message']['content']
            return {'response': assistant_response}
        except (KeyError, IndexError) as e:
            logging.error(f"Erro ao processar resposta da OpenAI: {str(e)}")
            return {'error': 'Erro ao processar resposta da API'}

# Exemplo de uso:
# openai_service = OpenAIService()
# result = openai_service.travel_assistant("Quero planejar uma viagem para a Europa em dezembro. O que sugere?")