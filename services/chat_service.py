"""
Serviço para manipulação de mensagens do chat
Este módulo fornece funções para adicionar, recuperar e processar mensagens do chat.
"""

import logging
from datetime import datetime
from flask import current_app, session

# Configurar logger
logger = logging.getLogger(__name__)

def add_system_message(session_id, message_content):
    """
    Adiciona uma mensagem do sistema ao chat

    Args:
        session_id: ID da sessão de chat
        message_content: Conteúdo da mensagem

    Returns:
        bool: True se a mensagem foi adicionada com sucesso, False caso contrário
    """
    try:
        logger.info(f"Adicionando mensagem de sistema à sessão {session_id}")
        
        # Verificar se a configuração de mensagens existe
        if 'chat_messages' not in current_app.config:
            current_app.config['chat_messages'] = {}
        
        # Verificar se a sessão existe
        if session_id not in current_app.config['chat_messages']:
            current_app.config['chat_messages'][session_id] = []
        
        # Adicionar mensagem
        message = {
            'content': message_content,
            'is_user': False,
            'timestamp': datetime.now().isoformat(),
            'message_type': 'system'
        }
        
        current_app.config['chat_messages'][session_id].append(message)
        
        # Tentar adicionar à sessão atual do usuário
        try:
            if 'messages' not in session:
                session['messages'] = []
            
            session['messages'].append(message)
            
            # Se temos a sessão do usuário, verificar se está vinculada ao session_id
            if 'session_id' not in session:
                session['session_id'] = session_id
        except Exception as e:
            logger.warning(f"Erro ao adicionar mensagem à sessão do usuário: {str(e)}")
        
        logger.info(f"Mensagem de sistema adicionada com sucesso à sessão {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao adicionar mensagem de sistema: {str(e)}")
        return False

def get_session_messages(session_id):
    """
    Recupera todas as mensagens de uma sessão de chat

    Args:
        session_id: ID da sessão de chat

    Returns:
        list: Lista de mensagens da sessão
    """
    try:
        # Verificar se a configuração de mensagens existe
        if 'chat_messages' not in current_app.config:
            return []
        
        # Verificar se a sessão existe
        if session_id not in current_app.config['chat_messages']:
            return []
        
        return current_app.config['chat_messages'][session_id]
        
    except Exception as e:
        logger.error(f"Erro ao recuperar mensagens da sessão {session_id}: {str(e)}")
        return []

def clear_session_messages(session_id):
    """
    Limpa todas as mensagens de uma sessão de chat

    Args:
        session_id: ID da sessão de chat

    Returns:
        bool: True se as mensagens foram limpas com sucesso, False caso contrário
    """
    try:
        # Verificar se a configuração de mensagens existe
        if 'chat_messages' not in current_app.config:
            return True
        
        # Verificar se a sessão existe
        if session_id not in current_app.config['chat_messages']:
            return True
        
        # Limpar mensagens
        current_app.config['chat_messages'][session_id] = []
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao limpar mensagens da sessão {session_id}: {str(e)}")
        return False