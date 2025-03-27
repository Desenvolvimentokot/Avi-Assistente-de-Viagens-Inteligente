
import logging
import sys
from sqlalchemy import inspect, text
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """
    Configura o banco de dados inicial com as tabelas e dados necessários
    """
    try:
        # Criar todas as tabelas definidas nos modelos
        with app.app_context():
            db.create_all()
            logger.info("Tabelas criadas com sucesso.")
            
            # Verificar se existem usuários
            user_count = User.query.count()
            
            # Criar usuário de teste se não houver nenhum
            if user_count == 0:
                try:
                    test_user = User(
                        name="Usuário de Teste",
                        email="teste@example.com",
                        password="senha123"
                    )
                    db.session.add(test_user)
                    db.session.commit()
                    logger.info("Usuário de teste criado com sucesso.")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Erro ao criar usuário de teste: {str(e)}")
                    
    except Exception as e:
        logger.error(f"Erro ao configurar banco de dados: {str(e)}")
        print(f"Erro: {str(e)}")
        return False
        
    return True
    
if __name__ == "__main__":
    if setup_database():
        sys.exit(0)
    else:
        sys.exit(1)
