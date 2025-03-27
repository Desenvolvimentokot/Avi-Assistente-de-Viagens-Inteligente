
import os
import json
import logging
from services.openai_service import OpenAIService
from services.prompts import BUSCA_RAPIDA_PROMPT

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instanciar serviço OpenAI
openai_service = OpenAIService()

def process_message(message, history=None):
    """
    Processa uma mensagem do usuário no modo busca rápida
    
    Args:
        message (str): Mensagem do usuário
        history (list): Histórico de mensagens anteriores
        
    Returns:
        dict: Resposta processada
    """
    if history is None:
        history = []
    
    try:
        logger.info(f"Processando mensagem no modo busca rápida: {message[:50]}...")
        
        # Preparar o contexto específico para busca rápida
        system_context = BUSCA_RAPIDA_PROMPT
        
        # Chamar o assistente da OpenAI
        result = openai_service.travel_assistant(
            user_message=message,
            conversation_history=history,
            system_context=system_context
        )
        
        # Verificar se houve erro na chamada à API
        if 'error' in result:
            logger.error(f"Erro ao chamar a API OpenAI: {result['error']}")
            return {"error": True, "message": "Erro ao processar sua mensagem. Por favor, tente novamente em alguns instantes."}
        
        # Extrair a resposta principal
        assistant_response = result.get('response', '')
        
        # Verificar se a resposta contém um link de compra
        purchase_link = None
        if '[[LINK_COMPRA:' in assistant_response:
            import re
            link_match = re.search(r'\[\[LINK_COMPRA:(.*?)\]\]', assistant_response)
            if link_match:
                purchase_link = link_match.group(1).strip()
                # Remover o marcador do texto
                assistant_response = assistant_response.replace(link_match.group(0), '')
        
        # Montar resposta final
        response = {
            "response": assistant_response.strip()
        }
        
        # Adicionar link de compra se encontrado
        if purchase_link:
            response["purchase_link"] = purchase_link
        
        return response
        
    except Exception as e:
        logger.exception(f"Erro ao processar mensagem no modo busca rápida: {str(e)}")
        return {"error": True, "message": f"Ocorreu um erro inesperado: {str(e)}"}
