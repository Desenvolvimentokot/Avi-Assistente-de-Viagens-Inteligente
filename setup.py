
import os
from app import app, db, User

# Cria as tabelas do banco de dados
with app.app_context():
    db.create_all()
    
    # Criar um usuário padrão se não existir nenhum
    if User.query.count() == 0:
        default_user = User(
            name="João Silva",
            email="joao.silva@exemplo.com",
            phone="+55 11 98765-4321",
            preferred_destinations="Praia, Montanha",
            accommodation_type="Hotel",
            budget="Médio"
        )
        default_user.set_password("senha123")
        db.session.add(default_user)
        db.session.commit()
        
        print("Usuário padrão criado com sucesso!")
        print("Email: joao.silva@exemplo.com")
        print("Senha: senha123")
    else:
        print("Banco de dados já inicializado.")
