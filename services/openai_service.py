import os
import logging
import requests
import json

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
            logging.info(f"Enviando requisição para OpenAI API...")
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
        Especialização do assistente para planejamento de viagens
        
        Parâmetros:
        - user_message: mensagem do usuário
        - conversation_history: histórico da conversa
        - system_context: contexto adicional para o sistema
        """
        if conversation_history is None:
            conversation_history = []
        
        # Importar os prompts do Avi
        from services.prompts.avi_system_prompt import AVI_SYSTEM_PROMPT
        from services.prompts.busca_rapida_prompt import BUSCA_RAPIDA_PROMPT
        from services.prompts.planejamento_completo_prompt import PLANEJAMENTO_COMPLETO_PROMPT
        
        # Identificar o contexto atual com base na mensagem e histórico
        # Por padrão, usamos o prompt base
        current_prompt = AVI_SYSTEM_PROMPT
        
        # Verificar se há um contexto específico de modo de busca
        if "busca rápida" in user_message.lower() or any("busca rápida" in msg.get('content', '').lower() for msg in conversation_history if msg.get('is_user', False)):
            current_prompt += "\n\n" + BUSCA_RAPIDA_PROMPT
        elif "planejamento completo" in user_message.lower() or any("planejamento completo" in msg.get('content', '').lower() for msg in conversation_history if msg.get('is_user', False)):
            current_prompt += "\n\n" + PLANEJAMENTO_COMPLETO_PROMPT
            
        # Criação do sistema de mensagens com o contexto da Avi
        base_system_content = current_prompt
        
        # Adicionar funcionalidades específicas
        base_system_content += """
            Funcionalidades da Avi:
            
            1. Ajudar os usuários a planejar viagens completas
            2. Recomendar destinos com base nos interesses e preferências do usuário
            3. Sugerir acomodações, restaurantes, atrações e atividades
            4. Fornecer informações sobre voos, transporte local e requisitos de viagem
            5. Responder dúvidas sobre destinos, clima, cultura local, e dicas de viagem
            6. Montar itinerários personalizados com base nas necessidades do usuário
            
            Instruções de processamento:
            
            - Analise cuidadosamente as menções de datas como períodos aproximados (ex: "primeira semana de novembro", "no mês de janeiro")
            - Quando um período aproximado for mencionado, identifique o intervalo de datas exato correspondente
            - Extraia dados específicos como origem, destino, datas, número de pessoas e preferências
            - Identifique e armazene informações importantes mesmo que o usuário as mencione em diferentes mensagens
            
            Instruções específicas:
            
            - Responda sempre em português brasileiro
            - Seja amigável, prestativo e entusiasmado sobre viagens
            - Personalize suas respostas de acordo com as preferências do usuário
            - Quando falar de preços, utilize o Real (R$) como moeda
            - Sugira destinos específicos e com detalhes quando o usuário pedir recomendações
            - Não seja excessivamente prolixo, seja conciso e direto quando necessário
            - Quando apresentar opções de voos ou hotéis, indique claramente como o usuário pode realizar a compra
        """
            
        # Adicionar contexto específico do sistema, se fornecido
        if system_context:
            base_system_content += f"\n\n{system_context}"
            
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