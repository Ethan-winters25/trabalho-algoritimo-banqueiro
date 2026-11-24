# Trabalho 3 – Simulador do Algoritmo do Banqueiro

Simulador em Python 3 para a disciplina de **Sistemas Operacionais**. O programa
trabalha com um único tipo de recurso e compara duas formas de alocação:

- **Versão 1 – Algoritmo do Banqueiro (Dijkstra, 1965):** evita impasses
  verificando se o estado resultante de cada requisição continua seguro antes de
  conceder os recursos.
- **Versão 2 – Alocação Ingênua / FCFS (First-Come, First-Served):** concede
  qualquer requisição que caiba no saldo disponível no instante, sem verificar a
  segurança futura.

## Versão 1 – Algoritmo do Banqueiro

### Como funciona

A cada requisição `REQ <processo> <quantidade>`, a função `solicitar_recurso`:

1. localiza o processo e verifica se ele existe;
2. rejeita quantidade não positiva ou acima da necessidade restante
   (`maximo - possui`);
3. rejeita pedidos maiores que o disponível no momento;
4. simula a concessão em uma **cópia profunda** do estado;
5. executa `esta_seguro` na cópia: se o estado resultante for seguro, efetiva a
   alocação; caso contrário, **nega** o pedido e mantém o estado original
   (rollback);
6. se o processo atingir o máximo, ele conclui e devolve todos os recursos ao
   sistema.

Assim, o estado real só muda quando existe pelo menos uma sequência segura de
conclusão para todos os processos ativos.

### Execução a partir de arquivos

`executar_arquivos(caminho_json, caminho_req)` lê o estado inicial, valida os
dados, exibe a tabela de recursos, informa se o estado inicial é seguro e
processa todas as linhas do arquivo de requisições, mostrando o resultado de
cada pedido e o estado final do sistema.

O formato de estado escolhido é **JSON**:

```json
{
  "total": 10,
  "processos": [
    {"nome": "A", "possui": 1, "maximo": 6},
    {"nome": "B", "possui": 1, "maximo": 5},
    {"nome": "C", "possui": 2, "maximo": 4},
    {"nome": "D", "possui": 4, "maximo": 7}
  ]
}
```

O arquivo de requisições é um `.txt` com uma requisição por linha, no formato
`REQ <processo> <quantidade>`. Linhas vazias e linhas iniciadas por `#` são
ignoradas:

```text
# Exemplo
REQ B 1
REQ C 2
```

```python
from pathlib import Path
from main import executar_arquivos

executar_arquivos(Path("testes/t2.json"), Path("testes/req_t4.txt"))
```

## Versão 2 – Alocação Ingênua / FCFS

### Como funciona

1. O processo pede uma quantidade de recursos.
2. Se a quantidade couber no disponível atual, o FCFS **concede imediatamente**,
   sem simular o estado resultante e sem testar segurança.
3. Se não couber, o processo fica **bloqueado** aguardando uma liberação.
4. Se todos os processos ativos ficarem bloqueados e nenhum conseguir atingir
   seu máximo com o saldo restante, o sistema está em **deadlock**.

### Por que escolhemos o FCFS?

A política **FCFS** foi escolhida por ser o oposto mais simples e didático do
Algoritmo do Banqueiro: ela atende por ordem de chegada ("tem no cofre,
entrega") e não faz nenhum teste de segurança. Com isso, fica fácil mostrar na
prática o que o Banqueiro evita.

Sobre a mesma entrada do **T4** (`testes/t2.json` + `REQ B 1`):

- o **Banqueiro** simula a concessão, percebe que o estado resultante é inseguro
  (o disponível cai para 1) e **nega** o pedido, preservando o sistema;
- o **FCFS** concede o pedido sem verificar nada, o disponível cai para 1 e o
  sistema entra em **estado inseguro**. Na sequência completa de
  `testes/req_v2_deadlock.txt`, todos os processos ficam bloqueados e ocorre
  **deadlock**.

## Funções principais

| Função | Responsabilidade |
| :--- | :--- |
| `ler_input` | Lê o JSON de estado e devolve `(total, processos)`. |
| `ler_requisicoes` | Lê o arquivo `.txt` e devolve a lista de `(processo, quantidade)`. |
| `calcular_disponivel` | Calcula `total - soma(possui)` dos processos. |
| `validar_estado` | Valida o estado inicial (total, alocações e limites máximos). |
| `esta_seguro` | Executa a verificação de estado seguro e devolve a sequência segura. |
| `solicitar_recurso` | Versão 1: simula, testa a segurança e concede ou nega com rollback. |
| `executar_arquivos` | Executa a Versão 1 a partir dos arquivos de estado e de requisições. |
| `solicitar_recurso_fcfs` | Versão 2: concede pelo saldo atual, sem teste de segurança. |
| `verificar_deadlock_fcfs` | Versão 2: diagnostica estado inseguro ou deadlock. |
| `executar_requisicoes_fcfs` | Versão 2: processa uma sequência de requisições. |
| `executar_comparacao` | Compara as duas versões sobre o mesmo estado e as mesmas requisições. |
| `executar_testes` | Executa os casos obrigatórios T1 a T5 da Versão 1. |

### Estilização (`estilo.py`)

| Função | Responsabilidade |
| :--- | :--- |
| `estilizar` | Aplica cor e/ou negrito a um texto quando o terminal suporta ANSI. |
| `colorir_status` | Destaca automaticamente os status das mensagens (`CONCEDIDA`, `NEGADA`, `BLOQUEADO`, `INSEGURO`, `DEADLOCK DETECTADO` etc.). |
| `imprimir_secao` | Imprime cabeçalhos de seção em negrito e ciano. |

## Estrutura do projeto

```text
main.py                      # leitura, algoritmo do banqueiro, FCFS e testes
estilo.py                    # cores ANSI, negrito e cabeçalhos do terminal
testes/
  t1.json                    # T1: todos os processos sem recursos
  t2.json                    # T2: estado parcialmente alocado
  t3.json                    # T3: estado inseguro
  req_t4.txt                 # T4: REQ B 1
  req_t5.txt                 # T5: REQ C 2
  req_v2_deadlock.txt        # sequência que leva a Versão 2 ao deadlock
  saidas_esperadas.txt       # saídas esperadas dos testes
```

## Como executar

Pré-requisito: Python 3.9 ou superior (apenas biblioteca padrão). Não há etapa
de compilação; execute o script diretamente.

Por padrão, o programa exibe apenas a demonstração/comparação entre as duas
versões, sem executar os testes automatizados:

```bash
python main.py
```

Para executar **somente** os testes obrigatórios **T1 a T5**:

```bash
python main.py --testes
# ou
python main.py -t
```

O modo `--testes` não executa a comparação, e o modo padrão não executa os
testes. A comparação da **Versão 1** com a **Versão 2 (FCFS)** inclui os testes
**T6** (concessão insegura) e **T7** (deadlock).

Para processar um par específico de arquivos (estado + requisições) pela Versão
1, use `executar_arquivos` conforme o exemplo da seção
[Versão 1 – Execução a partir de arquivos](#execução-a-partir-de-arquivos).

## Saída colorida

A estilização fica isolada em `estilo.py` e é aplicada somente na impressão; as
funções de lógica continuam retornando texto puro. As cores seguem o significado
de cada status:

- **verde + negrito:** `CONCEDIDA` e estados seguros;
- **vermelho + negrito:** `NEGADA`, `ERRO`, `INSEGURO` e `DEADLOCK DETECTADO`;
- **amarelo + negrito:** `BLOQUEADO` e avisos de `ATENÇÃO`;
- **ciano + negrito:** títulos de seção e marcadores de teste;
- **negrito:** cabeçalhos da tabela e linha de total/disponível;
- **azul:** linhas separadoras da tabela.

As cores são ativadas automaticamente quando a saída é um terminal compatível.
Para desativar, defina `NO_COLOR=1`; para forçar as cores mesmo em saídas
redirecionadas (útil em logs), defina `FORCE_COLOR=1`. `NO_COLOR` tem
precedência sobre `FORCE_COLOR`.

## Casos de teste

### Versão 1 – Algoritmo do Banqueiro

| Teste | Entrada | Disponível | Resultado esperado |
| :---: | :--- | :---: | :--- |
| **T1** | `testes/t1.json` | 10 | Seguro (sequência: A, B, C, D) |
| **T2** | `testes/t2.json` | 2 | Seguro (sequência: C, D, A, B) |
| **T3** | `testes/t3.json` | 1 | Inseguro |
| **T4** | `t2.json` + `req_t4.txt` (`REQ B 1`) | 2 | Negada (estado resultante inseguro) |
| **T5** | `t2.json` + `req_t5.txt` (`REQ C 2`) | 2 | Concedida (sequência segura: C, D, A, B) |

Saídas dos pedidos:

```text
REQ B 1 -> NEGADA (estado resultante inseguro)
REQ C 2 -> CONCEDIDA (sequência segura: C, D, A, B)
```

Todos os casos T1 a T5 passam na execução automatizada
(`python main.py --testes`).

### Versão 2 – Alocação Ingênua / FCFS

| Teste | Entrada | Disponível inicial | Resultado esperado |
| :---: | :--- | :---: | :--- |
| **T6** | `t2.json` + `req_t4.txt` (`REQ B 1`) | 2 | Concede sem verificação; disponível cai para 1 e o sistema fica inseguro |
| **T7** | `t2.json` + `req_v2_deadlock.txt` | 2 | Concede `REQ B 1`, bloqueia C, D, A e B e detecta **deadlock** |

As saídas detalhadas estão em `testes/saidas_esperadas.txt`.
