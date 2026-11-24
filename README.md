# Trabalho 3 – Simulador do Algoritmo do Banqueiro

Simulador em Python 3 para a disciplina de **Sistemas Operacionais**. O programa
trabalha com um único tipo de recurso e compara duas formas de alocação:

- **Versão 1 – Algoritmo do Banqueiro (Dijkstra, 1965):** evita impasses
  verificando se o estado resultante de cada requisição continua seguro antes de
  conceder os recursos.
- **Versão 2 – Alocação Ingênua / FCFS (First-Come, First-Served):** concede
  qualquer requisição que caiba no saldo disponível no instante, sem verificar a
  segurança futura.

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

## Estrutura do projeto

```text
main.py                      # leitura, algoritmo do banqueiro e FCFS
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

Pré-requisito: Python 3.9 ou superior (apenas biblioteca padrão).

```bash
python main.py
```

O programa executa:

1. os testes obrigatórios **T1 a T5** da Versão 1;
2. a comparação da **Versão 1** com a **Versão 2 (FCFS)**, incluindo os testes
   **T6** (concessão insegura) e **T7** (deadlock).

## Casos de teste

### Versão 1 – Algoritmo do Banqueiro

| Teste | Entrada | Disponível | Resultado esperado |
| :---: | :--- | :---: | :--- |
| **T1** | `testes/t1.json` | 10 | Seguro (sequência: A, B, C, D) |
| **T2** | `testes/t2.json` | 2 | Seguro (sequência: C, D, A, B) |
| **T3** | `testes/t3.json` | 1 | Inseguro |
| **T4** | `t2.json` + `req_t4.txt` (`REQ B 1`) | 2 | Negada (estado resultante inseguro) |
| **T5** | `t2.json` + `req_t5.txt` (`REQ C 2`) | 2 | Concedida (sequência segura: C, D, A, B) |

### Versão 2 – Alocação Ingênua / FCFS

| Teste | Entrada | Disponível inicial | Resultado esperado |
| :---: | :--- | :---: | :--- |
| **T6** | `t2.json` + `req_t4.txt` (`REQ B 1`) | 2 | Concede sem verificação; disponível cai para 1 e o sistema fica inseguro |
| **T7** | `t2.json` + `req_v2_deadlock.txt` | 2 | Concede `REQ B 1`, bloqueia C, D, A e B e detecta **deadlock** |

As saídas detalhadas estão em `testes/saidas_esperadas.txt`.