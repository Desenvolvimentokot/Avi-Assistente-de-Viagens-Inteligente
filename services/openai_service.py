import os
import logging
import requests
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    """
    Serviço para interagir com a API OpenAI para processamento de linguagem natural
    """

    def __init__(self):
        """
        Inicializa o serviço OpenAI com a chave de API e configurações
        """
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"

        if not self.api_key:
            logger.warning("OPENAI_API_KEY não configurada. Configure nos Secrets do Replit.")

    def generate_text(self, prompt, model="gpt-3.5-turbo", max_tokens=500):
        """
        Gera texto usando a API OpenAI

        Args:
            prompt (str): O texto para continuar ou responder
            model (str): O modelo a ser usado (padrão: gpt-3.5-turbo)
            max_tokens (int): Número máximo de tokens a serem gerados

        Returns:
            str: Texto gerado ou mensagem de erro
        """
        if not self.api_key:
            return "Chave da API OpenAI não configurada"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )

            response.raise_for_status()
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return "Nenhuma resposta gerada"

        except Exception as e:
            error_message = f"Erro ao gerar texto com OpenAI: {str(e)}"
            logger.error(error_message)
            return error_message