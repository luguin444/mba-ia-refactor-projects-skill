# Catálogo de anti-patterns

Usado na **Fase 2**. 34 entradas.

Cada entrada descreve o anti-pattern por **sinal observável**, não por sintaxe de uma linguagem. A tabela de manifestações mostra como o mesmo sinal aparece em cada stack. Suportar uma stack nova significa acrescentar uma linha — o sinal e a severidade não mudam.

Regra de uso: procure o **sinal**. Se ele estiver presente, o finding existe, independentemente de quão sofisticado o código em volta pareça.

---

## CRITICAL

### AP-01 — Injeção de SQL por concatenação
**Sinal:** query montada por concatenação, interpolação ou template string contendo valor vindo de request, argumento de função pública ou parâmetro de rota.
**Manifestações:** Python `"SELECT * FROM t WHERE id = " + str(id)`, f-string em `cursor.execute` · JS `` `SELECT * FROM t WHERE id = ${id}` `` · qualquer stack: `WHERE 1=1` seguido de `query +=`.
**Severidade:** CRITICAL sempre. Não rebaixe para MEDIUM só porque "usar ORM facilitaria" — o achado é a injeção, não a ergonomia.
**Atenção:** o mesmo arquivo pode usar placeholders corretamente em um ponto e concatenar em outro. Verifique todas as queries.
**Transformação:** → PB-01

### AP-02 — Endpoint perigoso exposto sem proteção
**Sinal:** rota que executa entrada do cliente como código ou query, ou que apaga dados em massa, sem verificação de identidade.
**Manifestações:** `POST /admin/query` recebendo SQL no body · `POST /admin/reset-db` · `eval`/`exec` sobre o request · endpoint que dispara migração ou seed.
**Por que CRITICAL:** a severidade se ancora no pior caso — dump de credenciais ou `DROP TABLE`, não na lentidão de uma query pesada.
**Transformação:** → PB-13 (remoção; é exceção de contrato declarada)

### AP-03 — Segredo hardcoded
**Sinal:** literal com aparência de credencial atribuído a constante, campo de config ou argumento de conexão.
**Onde procurar:** código-fonte · arquivos de config versionados · manifesto.
**Manifestações:** Python `app.config['SECRET_KEY'] = '...'`, `smtplib.login('user', 'senha')` · JS `const config = { dbPass: '...', apiKey: 'pk_live_...' }` · geral: strings com prefixo `sk_`, `pk_`, `AKIA`, `ghp_`, `xoxb-`, ou chaves nomeadas `password`, `secret`, `token`, `key`.
**Transformação:** → PB-02

### AP-04 — Dado sensível em log ou resposta
**Sinal:** credencial, hash, número de cartão, token ou chave aparecendo em saída de log ou no corpo de uma resposta HTTP.
**Onde procurar:** chamadas de log · funções de serialização (`to_dict`, `toJSON`, `serialize`) · literais dentro de `jsonify`/`res.json`.
**Manifestações:** `console.log(\`cartão ${cc} chave ${apiKey}\`)` · `to_dict()` incluindo o campo `password` · endpoint de health devolvendo `secret_key`.
**Por que CRITICAL:** transforma má prática interna em vazamento externo. Um serializer que inclui a senha faz de toda rota que o usa um endpoint de exfiltração.
**Transformação:** → PB-14 (exceção de contrato declarada)

### AP-05 — Hash de senha ausente, caseiro ou obsoleto
**Sinal:** senha armazenada em claro; **ou** algoritmo implementado à mão; **ou** função de hash de propósito geral usada para senha.
**Manifestações:** comparação direta `senha == row['senha']` · `hashlib.md5(pwd)`, `sha1`, `sha256` sem derivação · loop próprio concatenando base64 · `crypto.createHash` para senha.
**Regra:** não avalie a qualidade do algoritmo. Implementação própria é o sinal, por si só. Custo computacional alto não é segurança — um loop de 10.000 iterações que trunca o resultado em 10 caracteres tem entropia quase nula e foi escrito para *parecer* key stretching.
**Transformação:** → PB-05

### AP-06 — God class / God module
**Sinal:** um arquivo ou classe concentra duas ou mais das quatro responsabilidades (conexão, query, regra de negócio, HTTP), ou atende três ou mais domínios distintos.
**Severidade:** **CRITICAL** quando o mesmo arquivo concentra acesso a dados **e** roteamento HTTP — o colapso completo das camadas. **HIGH** quando concentra duas responsabilidades sem juntar dados e roteamento, ou quando atende três ou mais domínios sem o colapso. Declare no finding qual das duas condições se aplica, e reporte na seção da severidade resultante.
**Manifestações:** classe chamada `Manager`, `Helper`, `Service` sem qualificador de domínio · módulo com funções de 4 entidades diferentes · arquivo de rota entre os maiores do projeto.
**Transformação:** → PB-03

### AP-07 — Autenticação ausente ou simulada
**Sinal:** rotas que alteram dados ou expõem dado de terceiro sem verificação de identidade; **ou** um endpoint de login que não emite credencial verificável; **ou** token previsível ou não assinado.
**Severidade:** **CRITICAL** quando alguma rota exposta devolve dado de outro usuário ou permite escrita destrutiva. **HIGH** quando o acesso é apenas de leitura de dado não sensível. Declare qual condição se aplica.
**Manifestações:** `'token': 'fake-jwt-token-' + str(user.id)` · login que valida a senha e devolve o usuário sem emitir nada · nenhuma rota lendo header de autorização · rota `/admin` pública · **rota com id de sujeito no caminho que exige apenas credencial, sem checar dono** — qualquer usuário logado opera sobre o recurso de qualquer outro.
**Corrigir.** Esta entrada já não é decisão de produto: o código diz quais rotas expõem dado de terceiro e quais fazem escrita, e isso basta para decidir o que proteger. O que a recomendação precisa declarar, **rota por rota**, é quais passam a exigir credencial e quais permanecem públicas com o motivo — um fluxo de cadastro ou de compra que é o único caminho de entrada do usuário permanece público, e isso se escreve na recomendação, não se omite.
**Transformação:** → PB-24

### AP-34 — Privilégio atribuído por entrada do cliente
**Sinal:** campo que determina papel, permissão, plano, limite ou preço lido do corpo ou da query da requisição e persistido sem verificar quem está pedindo.
**Severidade:** **CRITICAL.** É escalonamento de privilégio: não exige falha em outra camada nem conhecimento prévio, só um campo a mais no JSON.
**Manifestações:** Python `role = data.get('role', 'user')` seguido de `user.role = role` num cadastro público · JS `{ plan: req.body.plan }` · geral: `is_admin`, `permissions`, `tier`, `discount` ou `price` vindos do cliente.
**Independente do AP-07.** Corrigir isto **não exige autenticação nenhuma** — basta parar de ler o campo do corpo e usar o default do servidor. Reporte separado, mesmo quando o AP-07 também estiver presente; empacotar os dois num finding só faz a correção trivial ser adiada junto com a difícil.
**Como confirmar:** dispare o cadastro público com o campo privilegiado no corpo e leia o registro criado. Se o valor entrou, o finding existe.
**Transformação:** → PB-25

### AP-08 — Modo debug habilitado em bind público
**Sinal:** flag de debug ou verbose ligada junto com bind em interface não-local.
**Manifestações:** `app.run(debug=True, host='0.0.0.0')` · `DEBUG = True` em config versionada · `NODE_ENV` ausente com stack trace na resposta.
**Por que CRITICAL:** o console interativo do Werkzeug exposto na rede é execução remota de código, não inconveniência.
**Transformação:** → PB-02

### AP-33 — Integração crítica substituída por stub
**Sinal:** decisão de negócio de alto impacto — cobrança, autorização, verificação de identidade, comunicação obrigatória — tomada por expressão local trivial, onde o domínio exige chamada a um serviço externo. Sinais auxiliares: resultado derivado de prefixo, sufixo, comprimento ou valor mágico do input; credencial de gateway declarada na config e nunca lida por quem decide; função de envio que só registra log.
**Severidade:** **CRITICAL** quando o stub decide dinheiro, acesso ou identidade. **HIGH** nos demais casos. Declare qual condição se aplica.
**Manifestações:** JS `cc.startsWith("4") ? "PAID" : "DENIED"` · geral `def verificar(...): return True` · geral: `paymentGatewayKey` no config e nenhuma chamada HTTP ao gateway · geral: `enviar_email()` que só imprime.
**Não confundir com AP-09.** O AP-09 é sobre a regra estar na **camada errada**; este é sobre a regra ser **falsa**, onde quer que esteja. Uma decisão de pagamento resolvida por um caractere é os dois findings ao mesmo tempo, e é este que define a severidade.
**Por que importa:** receita fabricada e produto liberado de graça, sem nenhum erro no log. O stub se parece com lógica, então revisão de código passa por cima.
**Transformação:** → PB-23 — e o finding **permanece** em `REQUER DECISÃO DE PRODUTO`: uma refatoração que preserva contrato não pode inventar a integração que não existe.

> **Nota de numeração:** esta entrada é AP-33 e vive na seção CRITICAL. A numeração é identificador estável, não posição — relatórios já emitidos referenciam AP-NN, e renumerar quebraria o rastro.

---

## HIGH

### AP-09 — Regra de negócio na camada errada
**Sinal:** cálculo de domínio, faixa de valor, transição de estado ou validação de regra dentro de um handler HTTP **ou** dentro de uma função de acesso a dados.
**Manifestações:** controller conferindo estoque · repositório calculando desconto por faixa de faturamento · rota decidindo se uma entidade está atrasada.
**Atenção:** a violação acontece nas duas direções. Aponte a camada exata — errar isso invalida o finding.
**Transformação:** → PB-04

### AP-10 — Escrita multi-entidade sem transação
**Sinal:** duas ou mais escritas relacionadas sem transação explícita, ou sem rollback no caminho de erro.
**Manifestações:** inserir pedido, inserir itens e debitar estoque com um único commit ao final · escritas encadeadas em callbacks sem `BEGIN` · `except` que não chama rollback.
**Por que HIGH:** falha no meio deixa estado inconsistente — matrícula sem pagamento, estoque debitado sem venda.
**Transformação:** → PB-07

### AP-11 — Estado global mutável
**Sinal:** variável de módulo mutável compartilhada entre requisições.
**Manifestações:** singleton de conexão em variável global · cache em objeto de módulo que cresce sem limite · contador exportado do módulo.
**Atenção:** em JS, exportar um número ou string exporta **por valor** — quem importa recebe uma cópia congelada e nunca vê atualização. É bug latente, não só acoplamento.
**Transformação:** → PB-04

### AP-12 — Efeito colateral escondido no fluxo
**Sinal:** operação não anunciada pelo nome nem pelo contrato da rota.
**Manifestações:** checkout que cria conta de usuário silenciosamente, com senha default quando o campo vem vazio · controller disparando e-mail, SMS e push · getter que grava em log de auditoria.
**Transformação:** → PB-04

### AP-13 — Acesso a dados sem camada própria
**Sinal:** rota ou controller importando driver de banco, ORM ou montando query.
**Manifestações:** `from database import get_db` dentro do módulo de rotas · `this.db.run(...)` dentro do handler · `Model.query.filter(...)` no controller.
**Transformação:** → PB-03

### AP-14 — Camada decorativa
**Sinal:** símbolo definido na camada correta cuja contagem de referências no projeto é **1** — a própria definição — enquanto lógica equivalente aparece duplicada em outra camada.
**Como detectar:** para cada método público de model/service/helper, conte as ocorrências do nome no projeto. Contagem 1 = nunca chamado. Depois procure a lógica dele copiada nas rotas ou controllers.
**Manifestações:** `Task.is_overdue()` definido e a mesma condição copiada inline em cinco rotas · função de validação de payload escrita e nunca usada enquanto os handlers revalidam à mão · classe de serviço que ninguém instancia.
**Por que HIGH:** é pior que ausência de camada. A estrutura desarma a suspeita de quem lê rápido, e as cópias divergem entre si sem ninguém perceber.
**Transformação:** → PB-15

### AP-15 — Erro engolido silenciosamente
**Sinal:** caminho de erro que não trata, não registra e não propaga.
**Manifestações:** callback que recebe `err` e nunca o checa · `except:` nu · `catch {}` vazio · resposta 200 num caminho que falhou.
**Atenção:** `except:` sem tipo captura também `KeyboardInterrupt` e `SystemExit`.
**Transformação:** → PB-08

### AP-16 — Controle de fluxo assíncrono manual
**Sinal:** aninhamento profundo de callbacks, ou contadores decrementados à mão para decidir quando responder.
**Manifestações:** pirâmide de 4+ níveis · `let pending = items.length` com `pending--` dentro de cada callback · `const self = this` convivendo com arrow functions.
**Por que HIGH:** se um callback falha, o contador nunca zera e a requisição fica pendurada até o timeout do cliente.
**Transformação:** → PB-10

---

## MEDIUM

### AP-17 — Queries N+1
**Sinal:** consulta ao banco dentro de laço, iterador ou callback que já percorre um resultado anterior.
**Manifestações:** `for` sobre pedidos com uma query de itens por pedido · `forEach` com `db.get` dentro · contagem por linha de uma listagem · relacionamento do ORM declarado e ignorado em favor de busca manual.
**Dica:** variáveis numeradas (`cursor2`, `cursor3`) são sintoma quase certo.
**Como confirmar:** localize todo laço que percorre um resultado de query e procure chamada ao banco no corpo dele. Conte: `1 + N` para um nível, `1 + N + N*M` para dois.

```bash
grep -nE '(for|forEach|map)\b' <arquivo> ; # depois leia o corpo de cada um
grep -cE '\.(execute|query|get|all|run|find)\(' <arquivo>
```

Se o projeto usa ORM, procure `relationship`/`belongsTo` declarado e **não** usado: o relacionamento existir e a rota buscar à mão é N+1 com a solução já escrita ao lado.
**Transformação:** → PB-06

### AP-18 — Resposta não-determinística
**Sinal:** ordem ou conteúdo do corpo variando entre chamadas idênticas.
**Manifestações:** array montado por `push` dentro de callbacks concorrentes · listagem sem `ORDER BY` · agregação dependente de ordem de conclusão.
**Como confirmar:** chame o endpoint 5 a 10 vezes e compare. É o único anti-pattern deste catálogo que exige execução para ser provado.
**Por que importa:** quebra clientes que indexam o array, e torna qualquer diff de contrato inútil sem normalização.
**Transformação:** → PB-16

### AP-19 — API ou dependência deprecated
**Sinal:** uso de API marcada como obsoleta pela linguagem ou framework, ou dependência marcada como deprecated pelo registry.
**Onde procurar:** os três lugares — código-fonte, manifesto, lockfile.
**Manifestações:**

| Stack | Deprecated | Equivalente moderno |
|---|---|---|
| Python 3.12+ | `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| SQLAlchemy 2.x | `Model.query`, `Query.get()` | `db.session.get(Model, id)`, `select()` |
| Flask 2.3+ | `@app.before_first_request` | inicialização no factory |
| Node | `new Buffer()`, `url.parse()`, `crypto.createCipher` | `Buffer.from()`, `new URL()`, `createCipheriv` |
| Node 22+ | pacote `sqlite3` nativo com deps podres | `node:sqlite`, `better-sqlite3` |
| npm | pacote com campo `deprecated` no lock | versão corrente ou substituto |

**Severidade:** **MEDIUM** para deriva de versão sem vulnerabilidade conhecida, ou API obsoleta que ainda funciona. **HIGH** quando alguma dependência fixada tem CVE conhecido. **CRITICAL** quando o CVE atinge um mecanismo de segurança que o projeto usa de forma permissiva — CVE de casamento de origem num projeto com CORS liberado para todas as origens, por exemplo, porque as duas falhas se somam. Declare qual condição se aplica e cite os identificadores.

### Os três passos são obrigatórios, não oportunistas

O erro clássico desta entrada é esperar que um `DeprecationWarning` apareça. Boot silencioso **não é** evidência de ausência: uma dependência pode estar três versões atrás, com CVE, e não emitir aviso nenhum. Execute os três:

**1. Deriva de versão.** Para cada dependência direta, compare a versão fixada com a corrente. Nunca reporte "nenhuma dependência desatualizada" sem ter rodado isto.

```bash
pip index versions <pacote>          # Python — a primeira linha é a corrente
npm outdated                         # Node
```

**2. Vulnerabilidade conhecida.** Consulte a base pública para cada dependência direta, na versão fixada. É o passo que separa higiene de segurança.

```bash
# Python — OSV.dev, sem instalar nada
curl -s -X POST https://api.osv.dev/v1/query -H 'Content-Type: application/json' \
  -d '{"package":{"name":"flask-cors","ecosystem":"PyPI"},"version":"5.0.1"}' \
  | python3 -c "import sys,json; [print(v['id'], v.get('summary','')) for v in json.load(sys.stdin).get('vulns',[])]"

# Node
npm audit --json
```

**3. Sinais no código e no lockfile.** Os `DeprecationWarning` do boot, os `npm warn deprecated` do install, o campo `"deprecated"` no lockfile, e as APIs da tabela acima.

Um finding de AP-19 só pode ser omitido depois de os três passos terem rodado e voltado vazios. Se rodar o passo 2 não for possível no ambiente, diga isso no relatório em vez de concluir que não há vulnerabilidade.

**Transformação:** → PB-11

### AP-20 — Duplicação entre handlers irmãos
**Sinal:** dois handlers do mesmo recurso com blocos equivalentes, tipicamente criar e atualizar.
**Como confirmar a severidade:** compare os blocos. Se já divergiram, o finding tem impacto demonstrável — cite qual regra existe num e falta no outro.
**Transformação:** → PB-12

### AP-21 — Tratamento de erro repetido sem handler central
**Sinal:** o mesmo bloco de captura repetido em cada handler, e/ou mensagem crua da exceção devolvida ao cliente.
**Manifestações:** `except Exception as e: return jsonify({'erro': str(e)}), 500` em 17 funções · ausência de middleware de erro no framework · respostas de erro em texto puro enquanto o sucesso é JSON.
**Transformação:** → PB-08

### AP-22 — Contrato de resposta sem serializer único
**Sinal:** corpo da resposta montado por literal em cada ponto, sem fonte única de verdade.
**Manifestações:** o mesmo recurso com formatos diferentes dependendo da rota · dicionário montado campo a campo em vários lugares · serializer existindo e sendo ignorado por parte das rotas (ver AP-14).
**Como confirmar:** escolha o campo mais característico de cada entidade e conte em quantos arquivos ele é atribuído numa construção de resposta. Dois ou mais pontos para a mesma entidade = sem fonte única.

```bash
grep -rn "'nome'\|\"nome\":" --include='*.py' . | grep -vE 'test|migration'
```

**Quando não se aplica:** respostas pequenas e distintas entre si — `{msg, id}` num endpoint e `{msg, token}` noutro — não compartilham entidade e não precisam de serializer. Exija o padrão quando **a mesma entidade** é montada em dois lugares, não por haver literais.
**Transformação:** → PB-12

### AP-23 — Schema sem constraints de integridade
**Sinal:** DDL ou definição de model sem `NOT NULL`, `UNIQUE` ou `FOREIGN KEY` onde o domínio exige.
**Manifestações:** coluna de e-mail sem `UNIQUE` combinada com verifica-e-insere na aplicação (race de duplicata) · chave estrangeira ausente permitindo registro órfão.
**Como confirmar:** leia o DDL e conte. Toda coluna que o código trata como obrigatória precisa de `NOT NULL`; toda que o código consulta antes de inserir precisa de `UNIQUE`; toda que guarda id de outra tabela precisa de `FOREIGN KEY`.

```bash
grep -cE 'NOT NULL' <schema>   # compare com o nº de colunas obrigatórias
grep -cE 'UNIQUE'   <schema>
grep -cE 'REFERENCES|FOREIGN KEY' <schema>
```

Em SQLite, `FOREIGN KEY` declarada só é aplicada com `PRAGMA foreign_keys = ON` por conexão — declarar sem ligar é constraint decorativa, e conta como o finding.
**Transformação:** → PB-17

### AP-24 — Limpeza em cascata manual
**Sinal:** remoção de entidade pai percorrendo filhos em laço, ou não tratando os filhos.
**Manifestações:** `for t in tasks: session.delete(t)` antes de deletar o usuário · `DELETE FROM users` deixando matrículas e pagamentos apontando para id inexistente.
**Como confirmar por execução:** apague um pai que tem filhos e leia um endpoint que lista os filhos. Se aparecer `"Unknown"`, `null` ou id apontando para nada, o finding existe — e cite o valor observado no relatório.
**Transformação:** → PB-17

### AP-25 — Bootstrap acoplado à inicialização
**Sinal:** criação de schema ou inserção de dados de exemplo disparada por import, por obtenção de conexão, ou pelo boot.
**Manifestações:** seeds dentro de `get_db()` · `db.create_all()` em tempo de import · DDL no construtor.
**Por que importa:** dados fictícios entram em qualquer ambiente que importar o módulo, e não há versionamento de schema.
**Transformação:** → PB-18

### AP-26 — CORS irrestrito
**Sinal:** CORS habilitado sem restringir origem.
**Manifestações:** `CORS(app)` · `app.use(cors())` · header `Access-Control-Allow-Origin: *` fixo.
**Atenção:** presença de CORS configurado não é defesa. Liberado para tudo é o achado.
**Transformação:** → PB-02

---

## LOW

### AP-27 — Magic numbers e literais repetidos
**Sinal:** valor de domínio cravado no meio da lógica, ou lista de valores válidos repetida.
**Manifestações:** faixas de desconto `10000 / 5000 / 1000` com multiplicadores soltos · lista de status válidos repetida em cinco arquivos · limites de tamanho literais · número de versão cravado em dois ou mais lugares · metadado de ambiente fixo no código e **incoerente com o estado real do processo** (um `/health` que se declara `"ambiente": "producao"` enquanto reporta `"debug": true`).
**Agrava:** se existe uma constante definida para isso e os handlers repetem o literal mesmo assim, some ao AP-14. Metadado incoerente é pior que magic number comum — o endpoint de diagnóstico passa a mentir sobre o estado do serviço, que é exatamente o que ele existe para não fazer.
**Transformação:** → PB-19

### AP-28 — `print` como logging
**Sinal:** saída de diagnóstico por impressão direta, sem nível nem destino configurável.
**Manifestações:** `print(...)` / `console.log(...)` em caminho de erro ou auditoria · função de log própria que só imprime.
**Transformação:** → PB-20

### AP-29 — Nomes não descritivos
**Sinal:** identificador de uma letra fora de laço curto, numeração incremental, ou abreviação no contrato público.
**Manifestações:** `u`, `e`, `p`, `cc` para dados de negócio · `cursor2`, `cursor3` · campos de API `usr`, `eml`, `pwd`, `c_id`.
**Atenção:** `e` para um valor de negócio colide com a convenção de `error`.
**Transformação:** → PB-19

### AP-30 — Código e imports mortos
**Sinal:** símbolo cuja contagem de referências no projeto é 1, ou import nunca usado no arquivo.
**Diferença para AP-14:** aqui é só código morto. Se a lógica equivalente estiver duplicada em outra camada, é AP-14 e a severidade sobe para HIGH.
**Como confirmar:** para cada função, método público e constante, conte as ocorrências do nome no projeto. **Contagem 1 = só a definição = morto.** É o mesmo passo do AP-14, e roda uma vez servindo às duas entradas.

```bash
for s in $(grep -rhoE '^(def|class) [a-zA-Z_]+' . | awk '{print $2}' | sort -u); do
  n=$(grep -rho "\b$s\b" --include='*.py' . | wc -l)
  [ "$n" -le 1 ] && echo "morto: $s"
done
```

Depois, para cada símbolo morto, procure a lógica dele duplicada em outra camada: se existir, reclassifique como AP-14.
**Atenção:** import usado apenas como anotação de tipo (`sqlite3.Row`, `sqlite3.Connection`) **não** é morto. Confira o uso antes de apagar.
**Transformação:** → PB-21

### AP-31 — Ausência de paginação
**Sinal:** listagem carregando a tabela inteira, sem limite nem cursor.
**Manifestações:** `SELECT *` sem `LIMIT` · `Model.query.all()` seguido de serialização de tudo.
**Como confirmar:** liste as rotas de coleção e, para cada uma, verifique se a query tem cláusula de limite.

```bash
grep -rnE 'SELECT \*|\.all\(\)' --include='*.py' . | grep -v LIMIT
```

**Transformação:** → PB-22

### AP-32 — Verbosidade evitável
**Sinal:** construção que expressa em muitas linhas o que a linguagem expressa em uma.
**Manifestações:** `if cond: return True else: return False` · `type(x) == list` em vez de `isinstance` · concatenação com conversão explícita em vez de interpolação · `let` para valor nunca reatribuído.
**Transformação:** → PB-19
