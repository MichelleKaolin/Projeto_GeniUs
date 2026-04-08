"""Seed the database with initial subjects, achievements, challenges, and questions."""

from sqlalchemy.orm import Session

from app.models import Subject, Achievement, Challenge, Question, User
from app.auth import hash_password


def seed_subjects(db: Session) -> list[Subject]:
    existing = db.query(Subject).count()
    if existing > 0:
        return list(db.query(Subject).all())

    subjects_data = [
        {"name": "Algoritmos", "icon": "\U0001f4bb", "color_from": "#007AFF", "color_to": "#6000DD"},
        {"name": "Calculo I", "icon": "\U0001f522", "color_from": "#FF6B00", "color_to": "#FF2D55"},
        {"name": "Fisica", "icon": "\u2697\ufe0f", "color_from": "#00C851", "color_to": "#007AFF"},
        {"name": "Banco de Dados", "icon": "\U0001f5c4\ufe0f", "color_from": "#FFD60A", "color_to": "#FF6B00"},
        {"name": "Quimica", "icon": "\U0001f9ea", "color_from": "#FF2D55", "color_to": "#C0006B"},
        {"name": "Algebra Linear", "icon": "\U0001f4d0", "color_from": "#6000DD", "color_to": "#007AFF"},
        {"name": "Redes", "icon": "\U0001f310", "color_from": "#00C851", "color_to": "#FFD60A"},
        {"name": "Estatistica", "icon": "\U0001f4ca", "color_from": "#FF6B00", "color_to": "#FFD60A"},
    ]

    subjects = []
    for s in subjects_data:
        subj = Subject(**s)
        db.add(subj)
        subjects.append(subj)
    db.commit()
    for s in subjects:
        db.refresh(s)
    return subjects


def seed_achievements(db: Session) -> None:
    existing = db.query(Achievement).count()
    if existing > 0:
        return

    achievements_data = [
        {
            "name": "Sequencia de Fogo",
            "description": "10 dias seguidos estudando",
            "icon": "\U0001f525",
            "condition_type": "streak",
            "condition_value": 10,
        },
        {
            "name": "Primeiro Desafio",
            "description": "Complete seu primeiro desafio",
            "icon": "\u2b50",
            "condition_type": "challenges_completed",
            "condition_value": 1,
        },
        {
            "name": "Estudante Dedicado",
            "description": "Complete 50 desafios",
            "icon": "\U0001f4da",
            "condition_type": "challenges_completed",
            "condition_value": 50,
        },
        {
            "name": "Mestre do Quiz",
            "description": "Acerte 100 questoes",
            "icon": "\U0001f3af",
            "condition_type": "correct_answers",
            "condition_value": 100,
        },
        {
            "name": "Genio em Formacao",
            "description": "Alcance nivel 10",
            "icon": "\U0001f9e0",
            "condition_type": "level",
            "condition_value": 10,
        },
        {
            "name": "Competidor Nato",
            "description": "Participe de 10 competicoes",
            "icon": "\u2694\ufe0f",
            "condition_type": "competitions",
            "condition_value": 10,
        },
        {
            "name": "Imbativel",
            "description": "30 dias de sequencia",
            "icon": "\U0001f451",
            "condition_type": "streak",
            "condition_value": 30,
        },
        {
            "name": "XP Master",
            "description": "Acumule 10.000 XP",
            "icon": "\u26a1",
            "condition_type": "xp_total",
            "condition_value": 10000,
        },
    ]

    for a in achievements_data:
        db.add(Achievement(**a))
    db.commit()


def seed_questions(db: Session, subjects: list[Subject]) -> None:
    existing = db.query(Question).count()
    if existing > 0:
        return

    algo_subj = next((s for s in subjects if s.name == "Algoritmos"), subjects[0])
    calc_subj = next((s for s in subjects if s.name == "Calculo I"), subjects[1])
    phys_subj = next((s for s in subjects if s.name == "Fisica"), subjects[2])
    db_subj = next((s for s in subjects if s.name == "Banco de Dados"), subjects[3])

    # Create daily challenge for Algoritmos
    challenge1 = Challenge(
        subject_id=algo_subj.id,
        title="Algoritmos e Estruturas de Dados",
        description="Desafio diario de Algoritmos gerado por IA",
        xp_reward=200,
        question_count=5,
        is_daily=True,
        daily_date="",
    )
    db.add(challenge1)
    db.flush()

    algo_questions = [
        {
            "question_text": "Qual a complexidade de tempo do QuickSort no pior caso?",
            "options": ["O(n log n)", "O(n\u00b2)", "O(n)", "O(log n)"],
            "correct_answer_index": 1,
        },
        {
            "question_text": "Qual estrutura de dados usa LIFO (Last In First Out)?",
            "options": ["Fila", "Pilha", "Arvore", "Grafo"],
            "correct_answer_index": 1,
        },
        {
            "question_text": "O que e um algoritmo de busca binaria?",
            "options": [
                "Busca em lista nao ordenada",
                "Busca por forca bruta",
                "Divide e conquista em lista ordenada",
                "Busca em grafos",
            ],
            "correct_answer_index": 2,
        },
        {
            "question_text": "Qual o resultado de 2^10?",
            "options": ["512", "1024", "2048", "256"],
            "correct_answer_index": 1,
        },
        {
            "question_text": "O que e recursao?",
            "options": [
                "Repeticao com for",
                "Funcao que chama a si mesma",
                "Algoritmo de ordenacao",
                "Tipo de variavel",
            ],
            "correct_answer_index": 1,
        },
    ]

    for q_data in algo_questions:
        q = Question(
            challenge_id=challenge1.id,
            subject_id=algo_subj.id,
            xp_per_question=40,
            **q_data,
        )
        db.add(q)

    # Calculo challenge
    challenge2 = Challenge(
        subject_id=calc_subj.id,
        title="Calculo Diferencial",
        description="Desafio de Calculo I",
        xp_reward=200,
        question_count=5,
        is_daily=False,
    )
    db.add(challenge2)
    db.flush()

    calc_questions = [
        {
            "question_text": "Qual a derivada de f(x) = x^3?",
            "options": ["3x^2", "x^2", "3x", "x^3"],
            "correct_answer_index": 0,
        },
        {
            "question_text": "Qual o limite de (sen x)/x quando x tende a 0?",
            "options": ["0", "1", "Infinito", "Nao existe"],
            "correct_answer_index": 1,
        },
        {
            "question_text": "Qual a integral de 2x dx?",
            "options": ["x^2 + C", "2x^2 + C", "x + C", "2 + C"],
            "correct_answer_index": 0,
        },
        {
            "question_text": "A funcao f(x) = |x| e diferenciavel em x = 0?",
            "options": ["Sim", "Nao", "Depende do dominio", "Apenas pela esquerda"],
            "correct_answer_index": 1,
        },
        {
            "question_text": "Qual a regra da cadeia para d/dx[f(g(x))]?",
            "options": ["f'(x)*g'(x)", "f'(g(x))*g'(x)", "f(g'(x))", "f'(g(x))"],
            "correct_answer_index": 1,
        },
    ]

    for q_data in calc_questions:
        q = Question(
            challenge_id=challenge2.id,
            subject_id=calc_subj.id,
            xp_per_question=40,
            **q_data,
        )
        db.add(q)

    # Fisica challenge
    challenge3 = Challenge(
        subject_id=phys_subj.id,
        title="Mecanica Classica",
        description="Desafio de Fisica - Mecanica",
        xp_reward=200,
        question_count=5,
        is_daily=False,
    )
    db.add(challenge3)
    db.flush()

    phys_questions = [
        {
            "question_text": "Qual a segunda lei de Newton?",
            "options": ["F = m*a", "F = m*v", "E = m*c^2", "P = m*v"],
            "correct_answer_index": 0,
        },
        {
            "question_text": "Qual a unidade de forca no SI?",
            "options": ["Joule", "Newton", "Pascal", "Watt"],
            "correct_answer_index": 1,
        },
        {
            "question_text": "Um objeto em queda livre tem aceleracao de aproximadamente:",
            "options": ["5 m/s^2", "9.8 m/s^2", "15 m/s^2", "1 m/s^2"],
            "correct_answer_index": 1,
        },
        {
            "question_text": "Qual o principio da conservacao de energia?",
            "options": [
                "Energia pode ser criada",
                "Energia pode ser destruida",
                "Energia se transforma mas nao se cria nem se destroi",
                "Energia e sempre constante em qualquer sistema",
            ],
            "correct_answer_index": 2,
        },
        {
            "question_text": "Qual a formula da energia cinetica?",
            "options": ["Ec = m*g*h", "Ec = 1/2*m*v^2", "Ec = F*d", "Ec = P*t"],
            "correct_answer_index": 1,
        },
    ]

    for q_data in phys_questions:
        q = Question(
            challenge_id=challenge3.id,
            subject_id=phys_subj.id,
            xp_per_question=40,
            **q_data,
        )
        db.add(q)

    # Banco de Dados challenge
    challenge4 = Challenge(
        subject_id=db_subj.id,
        title="SQL e Modelagem de Dados",
        description="Desafio de Banco de Dados",
        xp_reward=200,
        question_count=5,
        is_daily=False,
    )
    db.add(challenge4)
    db.flush()

    db_questions = [
        {
            "question_text": "Qual comando SQL e usado para selecionar dados?",
            "options": ["INSERT", "SELECT", "UPDATE", "DELETE"],
            "correct_answer_index": 1,
        },
        {
            "question_text": "O que e uma chave primaria?",
            "options": [
                "Um campo opcional",
                "Um identificador unico para cada registro",
                "Um tipo de indice",
                "Uma restricao de tabela",
            ],
            "correct_answer_index": 1,
        },
        {
            "question_text": "Qual a diferenca entre INNER JOIN e LEFT JOIN?",
            "options": [
                "Nao ha diferenca",
                "INNER JOIN retorna apenas registros correspondentes",
                "LEFT JOIN retorna apenas registros da direita",
                "INNER JOIN e mais rapido",
            ],
            "correct_answer_index": 1,
        },
        {
            "question_text": "O que e normalizacao de banco de dados?",
            "options": [
                "Deletar dados duplicados",
                "Organizar dados para reduzir redundancia",
                "Criar backups",
                "Indexar tabelas",
            ],
            "correct_answer_index": 1,
        },
        {
            "question_text": "Qual clausula SQL filtra resultados apos GROUP BY?",
            "options": ["WHERE", "HAVING", "ORDER BY", "LIMIT"],
            "correct_answer_index": 1,
        },
    ]

    for q_data in db_questions:
        q = Question(
            challenge_id=challenge4.id,
            subject_id=db_subj.id,
            xp_per_question=40,
            **q_data,
        )
        db.add(q)

    db.commit()


def seed_demo_users(db: Session) -> None:
    existing = db.query(User).count()
    if existing > 0:
        return

    demo_users = [
        {
            "name": "Maria Silva",
            "email": "maria@universidade.edu.br",
            "password_hash": hash_password("password123"),
            "university": "Universidade Federal do Brasil",
            "course": "Eng. Computacao",
            "xp_total": 6240,
            "level": 18,
            "streak_days": 15,
            "streak_record": 22,
        },
        {
            "name": "Joao Pedro",
            "email": "joao@universidade.edu.br",
            "password_hash": hash_password("password123"),
            "university": "Universidade Federal do Brasil",
            "course": "Ciencia da Comp.",
            "xp_total": 5910,
            "level": 16,
            "streak_days": 8,
            "streak_record": 14,
        },
        {
            "name": "Alex Estudante",
            "email": "alex@universidade.edu.br",
            "password_hash": hash_password("password123"),
            "university": "Universidade Federal do Brasil",
            "course": "Engenharia de Computacao",
            "xp_total": 4820,
            "level": 14,
            "streak_days": 12,
            "streak_record": 18,
        },
        {
            "name": "Lucas Rodrigues",
            "email": "lucas@universidade.edu.br",
            "password_hash": hash_password("password123"),
            "university": "Universidade Federal do Brasil",
            "course": "Sistemas de Informacao",
            "xp_total": 4100,
            "level": 12,
            "streak_days": 5,
            "streak_record": 10,
        },
        {
            "name": "Carla Mendes",
            "email": "carla@universidade.edu.br",
            "password_hash": hash_password("password123"),
            "university": "Universidade Federal do Brasil",
            "course": "Eng. Computacao",
            "xp_total": 3880,
            "level": 11,
            "streak_days": 3,
            "streak_record": 8,
        },
        {
            "name": "Rafael Torres",
            "email": "rafael@universidade.edu.br",
            "password_hash": hash_password("password123"),
            "university": "Universidade Federal do Brasil",
            "course": "Ciencia da Comp.",
            "xp_total": 3500,
            "level": 10,
            "streak_days": 7,
            "streak_record": 12,
        },
    ]

    for u_data in demo_users:
        db.add(User(**u_data))
    db.commit()


def run_seed(db: Session) -> None:
    subjects = seed_subjects(db)
    seed_achievements(db)
    seed_questions(db, subjects)
    seed_demo_users(db)
