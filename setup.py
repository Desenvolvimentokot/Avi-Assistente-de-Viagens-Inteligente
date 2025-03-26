
from app import app, db
from models import User
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    with app.app_context():
        try:
            # Criar tabelas
            db.create_all()
            logger.info("Tabelas criadas com sucesso.")
            
            # Verificar se já existe um usuário de teste
            test_user = User.query.filter_by(username='teste').first()
            
            if not test_user:
                # Criar usuário de teste
                user = User(
                    username='teste',
                    email='teste@exemplo.com',
                    password_hash=generate_password_hash('senha123')
                )
                db.session.add(user)
                db.session.commit()
                logger.info("Usuário de teste criado com sucesso.")
            else:
                logger.info("Usuário de teste já existe.")
                
            return "Banco de dados já inicializado."
        except Exception as e:
            logger.error(f"Erro ao configurar banco de dados: {str(e)}")
            db.session.rollback()
            return f"Erro: {str(e)}"

if __name__ == '__main__':
    result = setup_database()
    print(result)
