
import os
import logging
from .openai_service import OpenAIService
from .prompts import BUSCA_RAPIDA_SYSTEM_PROMPT

class BuscaRapidaService:
    """
    Serviço especializado para o modo de Busca Rápida
    """
    def __init__(self):
        self.openai_service = OpenAIService()
        self.model = "gpt-4o"  # Usando o modelo mais avançado para melhor extração de dados
        
    def process_query(self, user_message, conversation_history=None):
        """
        Processa uma consulta do usuário no modo de Busca Rápida
        
        Parâmetros:
        - user_message: mensagem do usuário
        - conversation_history: histórico da conversa
        
        Retorna:
        - Resposta do assistente de busca rápida
        """
        if conversation_history is None:
            conversation_history = []
            
        # Usar o prompt específico de Busca Rápida como contexto do sistema
        messages = [
            {
                "role": "system",
                "content": BUSCA_RAPIDA_SYSTEM_PROMPT
            }
        ]
        
        # Adicionar histórico de conversa
        for msg in conversation_history:
            if msg.get('is_user'):
                messages.append({
                    "role": "user",
                    "content": msg.get('content', '')
                })
            else:
                messages.append({
                    "role": "assistant", 
                    "content": msg.get('content', '')
                })
        
        # Adicionar a mensagem atual do usuário
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Chamar a API do OpenAI com o modelo definido
        response = self.openai_service.create_chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
            model=self.model
        )
        
        if 'error' in response:
            logging.error(f"Erro na API do OpenAI: {response['error']}")
            return {'error': response['error']}
        
        try:
            # Extrair a resposta do assistente
            assistant_response = response['choices'][0]['message']['content']
            return {'response': assistant_response, 'model': self.model}
        except (KeyError, IndexError) as e:
            logging.error(f"Erro ao processar resposta do OpenAI: {str(e)}")
            return {'error': 'Erro ao processar resposta da API'}
