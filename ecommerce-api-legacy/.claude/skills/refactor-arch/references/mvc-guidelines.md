# Guidelines de arquitetura — MVC alvo

Usado na **Fase 3**. Define para onde o código vai e como verificar que chegou lá.

## As camadas

| Camada | Responsabilidade | Nunca faz |
|---|---|---|
| **config** | Lê configuração do ambiente e expõe tipada. Único lugar com valores por ambiente. | Conter literal sensível. Importar qualquer outra camada. |
| **models** | Representa a entidade e conversa com a persistência. Um módulo por domínio. | Importar nada de HTTP. Conter regra de negócio que atravessa entidades. |
| **controllers** | Orquestra o fluxo: valida entrada, chama a regra, monta a resposta. | Montar query ou SQL. Conter cálculo de domínio. |
| **views / routes** | Registra caminho, método e binding para o controller. Camada mais fina. | Importar driver de banco ou ORM. Conter lógica de qualquer tipo. |
| **middlewares** | Preocupações transversais: erro centralizado, CORS, logging, autenticação. | Conter regra de domínio. |
| **entry point** | Composition root: lê config, monta as dependências, registra rotas e middlewares, sobe o servidor. | Definir rota. Conter lógica. |

Duas camadas **opcionais**, criadas só quando o volume justifica:

| Camada | Quando criar |
|---|---|
| **services** | Regra de negócio que atravessa mais de uma entidade, ou orquestra efeito externo (e-mail, gateway). Um relatório que agrega 4 entidades justifica; um CRUD simples não. |
| **repositories** | Quando o acesso a dados tem complexidade própria — query composta, cache, mais de uma fonte. Com ORM enxuto, o model já basta. |

**Não crie camada vazia.** Uma pasta `services/` com um arquivo que ninguém instancia é exatamente o AP-14 que esta skill detecta. Se não há conteúdo para a camada, ela não existe.

## Estrutura

```
src/
├── config/          # configuração a partir do ambiente
├── models/          # um módulo por domínio
├── controllers/     # um módulo por domínio
├── views/           # ou routes/ — registro de rotas
├── middlewares/     # erro, CORS, log
└── <entry>.<ext>    # composition root
```

Nomes de arquivo por domínio, não por tipo genérico: `produto_model.py` e `pedido_controller.py`, não `model1.py`. Se o projeto já tem convenção de nomes, siga a dele.

## Regras verificáveis

Cada uma é checável por busca de texto. A Fase 3 não termina enquanto todas não passarem.

| # | Regra | Como verificar |
|---|---|---|
| L1 | Rotas não importam driver de banco nem ORM | buscar import de driver em `views/`/`routes/` — zero ocorrências |
| L2 | Controllers não montam query nem SQL | buscar SQL literal e `.execute(`/`.query(` em `controllers/` — zero |
| L3 | Models não importam nada de HTTP | buscar import do framework web em `models/` — zero |
| L4 | Nenhum literal sensível fora de `config/` | buscar os padrões do AP-03 no projeto — só em `config/`, e lendo do ambiente |
| L5 | Toda resposta de erro passa pelo middleware central | contar blocos de captura nos controllers — devem ser exceção, não regra |
| L6 | Nenhuma camada vazia ou não referenciada | cada módulo criado é importado por alguém |
| L7 | Entry point não define rota nem lógica | ler o arquivo — só composição |

## Adaptação ao ponto de partida

A Fase 1 classificou a arquitetura. O trabalho da Fase 3 muda conforme a classificação:

**Monolítica.** Reestruturação completa. Separe por domínio primeiro, por camada depois — quatro domínios misturados num arquivo viram quatro conjuntos model/controller, não uma pasta `models/` com um arquivo gigante.

**Camadas decorativas.** O trabalho é **devolver a responsabilidade à camada que já existe**, não criar pastas novas. Se um método está escrito no model e a lógica está copiada inline em cinco rotas, a transformação é apagar as cinco cópias e chamar o método. Criar estrutura nova aqui piora o problema.

**MVC parcial.** Ajuste dirigido: divida a camada sobrecarregada por domínio e mova o que estiver fora de lugar. Não reescreva o que já está correto.

## O que não fazer

- **Não renomeie rota, campo de resposta ou status code.** O contrato é preservado; as únicas exceções estão no SKILL.md e foram declaradas antes do gate.
- **Não adicione autenticação.** AP-07 fica marcado `REQUER DECISÃO DE PRODUTO`.
- **Não introduza dependência nova sem necessidade.** Trocar hash de senha justifica; trocar o framework web, não.
- **Não mova o que já está certo.** Movimentação sem ganho é risco de regressão sem contrapartida.
