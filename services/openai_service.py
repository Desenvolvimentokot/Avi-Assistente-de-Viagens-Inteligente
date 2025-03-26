import os
import logging
import requests
import json

class OpenAIService:
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.api_url = 'https://api.openai.com/v1/chat/completions'
        self.model = 'gpt-4o'
        
    def create_chat_completion(self, messages, temperature=0.7, max_tokens=1000):
        """
        Cria uma resposta usando a API de chat do OpenAI
        
        Parâmetros:
        - messages: lista de mensagens no formato esperado pela API
        - temperature: controle de aleatoriedade (0.0 a 1.0)
        - max_tokens: número máximo de tokens na resposta
        """
        if not self.api_key:
            logging.error("API key da OpenAI não configurada")
            return {'error': 'API key da OpenAI não configurada'}
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Erro na chamada à API OpenAI: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Resposta da API: {e.response.text}")
            return {'error': f'Erro na chamada à API OpenAI: {str(e)}'}
    
    def travel_assistant(self, user_message, conversation_history=None):
        """
        Especialização do assistente para planejamento de viagens
        
        Parâmetros:
        - user_message: mensagem do usuário
        - conversation_history: histórico da conversa
        """
        if conversation_history is None:
            conversation_history = []
        
        # Criação do sistema de mensagens com o contexto de assistente de viagem
        system_message = {
            "role": "system",
            "content": """Você é Flai, um assistente virtual especializado em planejamento de viagens.
            
            Suas responsabilidades incluem:
            
            1. Ajudar os usuários a planejar viagens completas
            2. Recomendar destinos com base nos interesses e preferências do usuário
            3. Sugerir acomodações, restaurantes, atrações e atividades
            4. Fornecer informações sobre voos, transporte local e requisitos de viagem
            5. Responder dúvidas sobre destinos, clima, cultura local, e dicas de viagem
            6. Montar itinerários personalizados com base nas necessidades do usuário
            
            Instruções específicas:
            
            - Responda sempre em português brasileiro
            - Seja amigável, prestativo e entusiasmado sobre viagens
            - Personalize suas respostas de acordo com as preferências do usuário
            - Quando falar de preços, utilize o Real (R$) como moeda
            - Sugira destinos específicos e com detalhes quando o usuário pedir recomendações
            - Não seja excessivamente prolixo, seja conciso e direto quando necessário
            """
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