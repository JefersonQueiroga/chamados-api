import random
from datetime import date, timedelta
from modelos import Chamado, LOCAIS, PRIORIDADES

QUANTIDADE_INICIAL = 8

MODELOS = [
    ("Ar-condicionado pingando", "Água escorrendo pela parede perto da porta", "climatização"),
    ("Ar-condicionado não liga", "Controle funciona, mas o aparelho não responde", "climatização"),
    ("Ventilador fazendo barulho", "Barulho alto na velocidade máxima", "climatização"),
    ("Sala muito quente", "Ar-condicionado liga, mas não gela", "climatização"),
    ("Lâmpada queimada", "Duas lâmpadas apagadas no fundo da sala", "elétrica"),
    ("Tomada sem energia", "Tomadas da bancada lateral não funcionam", "elétrica"),
    ("Disjuntor desarmando", "Cai sempre que ligam os computadores", "elétrica"),
    ("Interruptor quebrado", "Tecla solta, difícil de acender a luz", "elétrica"),
    ("Refletor da quadra apagado", "Um dos refletores não acende à noite", "elétrica"),
    ("Torneira vazando", "Pinga mesmo bem fechada", "hidráulica"),
    ("Descarga com defeito", "Descarga não para de correr água", "hidráulica"),
    ("Bebedouro sem água gelada", "Água saindo em temperatura ambiente", "hidráulica"),
    ("Pia entupida", "Água acumulando na pia", "hidráulica"),
    ("Vazamento no teto", "Goteira quando chove", "hidráulica"),
    ("Computador não liga", "Máquina 07 não dá sinal de vida", "informática"),
    ("Projetor sem imagem", "Liga, mas não reconhece o cabo HDMI", "informática"),
    ("Internet lenta", "Wi-Fi cai toda hora no período da tarde", "informática"),
    ("Teclado com teclas faltando", "Faltam as teclas A e S", "informática"),
    ("Mouse não funciona", "Cursor não se mexe em duas máquinas", "informática"),
    ("Impressora travando papel", "Papel enrosca a cada impressão", "informática"),
    ("Caixa de som chiando", "Chiado alto durante as apresentações", "informática"),
    ("Cadeira quebrada", "Encosto solto, risco de queda", "mobiliário"),
    ("Mesa bamba", "Pé da mesa do professor desnivelado", "mobiliário"),
    ("Quadro branco manchado", "Manchas que não saem com apagador", "mobiliário"),
    ("Porta não fecha", "Fechadura emperrada", "mobiliário"),
    ("Janela não abre", "Trinco travado", "mobiliário"),
    ("Armário sem chave", "Chave perdida, armário trancado", "mobiliário"),
    ("Persiana quebrada", "Persiana não desce, sol na tela do projetor", "mobiliário"),
    ("Lixeira cheia", "Lixeira transbordando desde ontem", "limpeza"),
    ("Banheiro sem papel", "Sem papel higiênico e sem papel toalha", "limpeza"),
    ("Chão molhado", "Poça perto da escada, risco de escorregar", "limpeza"),
    ("Sala com mau cheiro", "Cheiro forte vindo do ralo", "limpeza"),
    ("Formigas na cantina", "Formigas perto do balcão", "limpeza"),
    ("Saboneteira vazia", "Sem sabão em todas as pias", "limpeza"),
    ("Placa de sinalização caída", "Placa da saída de emergência no chão", "outro"),
    ("Extintor vencido", "Etiqueta com validade expirada", "outro"),
    ("Rede da quadra rasgada", "Rede de vôlei com rasgo grande", "outro"),
    ("Bicicletário com grade solta", "Grade se mexendo", "outro"),
    ("Cupim na estante", "Pó de madeira embaixo da estante", "outro"),
    ("Tela de proteção rasgada", "Mosquitos entrando pela janela", "outro"),
]

RESPONSAVEIS = ["Seu Raimundo", "Equipe de TI", "Dona Francisca", "Seu Antônio", "Equipe de manutenção", "Técnico do laboratório"]
SOLUCOES = ["Peça trocada", "Equipamento ajustado", "Limpeza realizada", "Conserto concluído", "Item substituído"]


def sortear_chamados(aluno):
    sorteio = random.Random(aluno.matricula)
    chamados = []
    for posicao, (titulo, descricao, tipo) in enumerate(sorteio.sample(MODELOS, QUANTIDADE_INICIAL)):
        dias_atras = sorteio.randint(2, 40)
        chamado = Chamado(
            aluno_id=aluno.id,
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            local=sorteio.choice(LOCAIS),
            prioridade=sorteio.choice(PRIORIDADES),
            data_abertura=date.today() - timedelta(days=dias_atras),
        )
        if posicao < 5:
            chamado.status = "em andamento"
            chamado.responsavel = sorteio.choice(RESPONSAVEIS)
        if posicao < 2:
            chamado.status = "resolvido"
            chamado.solucao = sorteio.choice(SOLUCOES)
            chamado.data_resolucao = chamado.data_abertura + timedelta(days=sorteio.randint(1, dias_atras - 1))
        chamados.append(chamado)
    return chamados
