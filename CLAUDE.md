# Agente de relacionamento e prospecção no LinkedIn — Manoel Gonçalves / Desenvolve Mais

Manual de continuidade. Objetivo comercial: construir relacionamentos que possam levar a contratos de consultoria, mentoria e desenvolvimento humano, pessoal e profissional.

**Tarefa prioritária:** organizar as conexões feitas em 2026, identificar as sem conversa anterior e preparar até **15 primeiras abordagens por dia útil**, com personalização real e **aprovação do Manoel antes de qualquer envio**.

> O código operacional vive em `G:\Meu Drive\GENOMA\GENOMA OS\linkedin-agent` (fora deste repositório). Este repositório guarda o manual e a documentação. Não publicar o repositório pai `GENOMA OS`.

## 1. Documentos a ler (nesta ordem, no projeto operacional)
1. `BROWSER_SESSION.md` — navegador autorizado e procedimento de envio
2. `ABORDAGEM.md` — abordagem atual das primeiras mensagens
3. `README.md` — funcionamento e comandos
4. `CLAUDE.md` — contexto técnico, regras e aprendizados
5. `config/icps.toml` — limites, horários, critérios de público, restrições de texto

`ESTRATEGIA.md` tem trechos antigos. Decisões posteriores prevalecem:
- Manoel e Desenvolve Mais são **uma única atuação, no mesmo perfil** (sem divisão de marcas nem proporção 60/40).
- A primeira mensagem é **abertura pessoal + pedido de permissão para compartilhar conteúdo** (não agradecimento genérico).
- A operação usa o **Chrome habitual do Manoel** (ver `BROWSER_SESSION.md`).

## 2. Responsabilidade da IA
Ler o banco e recuperar o ponto de continuidade; conferir conexões e históricos; ler perfis e reunir evidências; escrever mensagens individuais; organizar lotes e planejamento; apresentar textos concretos para aprovação; executar envios autorizados com as verificações exigidas; registrar resultados, falhas e pendências.

Ao Manoel cabem as decisões sobre pessoas, textos e continuidade comercial. **A IA não aprova mensagens em nome dele.** Quantidade de contatos não é relacionamento nem oportunidade.

## 3. Quem entra na fila
- Conexões desde **1º/jan/2026**, com inclusão contínua das novas.
- Somente **zero eventos** no histórico de conversa efetivamente carregado e conferido.
- Até **15 primeiros contatos por dia**, segunda a sexta, das conexões **mais antigas para as mais novas**.
- Qualquer conversa existente exclui a pessoa (inclusive só mensagem recebida).
- "Zero" não comprova ausência de contato em outros canais nem de mensagens apagadas.

| Estado | Significado | Tratamento |
|---|---|---|
| `unverified` | Histórico não conferido | Conferir antes de incluir em lote |
| `zero` | Nenhum evento após verificação | Pode entrar no planejamento |
| `has_history` | Existe conversa | Excluir da primeira abordagem |
| `contacted` | Marcado como contatado | Preservar, consultar evidências, não repetir |

Inventariar uma conexão não é verificar o histórico.

## 4. Conferência das conexões (a cada execução)
1. Ler registros existentes e preservar o progresso.
2. Confirmar pela interface a conta **Manoel Gonçalves**, perfil `/in/omanoelgoncalves/`.
3. Incorporar novas conexões sem duplicar perfis.
4. Conferir até **60 registros `unverified` por execução**.
5. Abrir a conversa do destinatário e aguardar o carregamento real.
6. Reler ou reabrir antes de concluir que está vazia (tela vazia ≠ `zero`).
7. Registrar estado e evidência. Em dúvida de identidade, carregamento ou histórico: manter pendente.

## 5. Primeira mensagem
Antes de redigir, abrir e ler o perfil atual: nome, cargo/atividade, empresa (se informada) e **um detalhe profissional real**. Uma publicação pode complementar, se pertinente e acessível.

Conteúdo: saudação pelo nome; abertura individual ligada ao trabalho real; referência ao conteúdo do Manoel sobre **como uma empresa pode estar faturando mais e ficando mais frágil ao mesmo tempo**; **no máximo uma pergunta**, pedindo permissão para compartilhar.

> Olá, [nome]. Vi no seu perfil [detalhe profissional efetivamente conferido]. Tenho um conteúdo sobre como uma empresa pode estar faturando mais e ficando mais frágil ao mesmo tempo. Posso compartilhar com você?

(Estrutura ilustrativa: exige adaptação após ler o perfil; personalização vai além de nome e cargo.)

Regras: tom humano, informal, respeitoso, objetivo. Sem link nem conteúdo completo; sem convite para reunião ou oferta; sem presumir problemas ou interesse; sem elogios ou resultados inventados; sem dizer que acompanhou/leu algo não conferido; sem afirmar "nunca conversamos" sem verificar; **sem mencionar Genoma Consultoria**; respeitar termos bloqueados da configuração. Faltou informação → manter pendente.

`outreach.save_personalized_draft(...)` exige trecho real do perfil como evidência e salva como **pendente**, sem aprovação automática.

## 6. Lotes e apresentação
Helpers: `outreach.plan_batches(...)` e `outreach.export_plan(...)` → `data/plano-contatos-2026.md` e `.html`.

Cada lote apresentado ao Manoel traz: pessoa (nome e perfil), contexto, personalização observada, **mensagem integral**, ID do rascunho, situação (pendente/aprovado/enviado/bloqueado). Data planejada **não autoriza** envio. A aprovação vale para destinatário e texto exatos; qualquer alteração exige nova aprovação.

## 7. Envio aprovado (Chrome habitual, perfil Manoel)
IDs de navegador/aba de sessões anteriores podem não existir: recuperar a aba e reconfirmar a identidade.
1. Consultar elegibilidade no banco (aprovação, destinatário, texto, sem tentativa anterior impeditiva).
2. Conferir hash do texto aprovado (quando houver snapshot).
3. Abrir a conversa correta: conta remetente, nome e identificador do destinatário.
4. Rever o histórico imediatamente antes; qualquer conversa existente cancela a abordagem.
5. Simulação (`preflight`): sem digitar nem clicar; validade até 24 h.
6. Preencher o editor com o texto exato (se houver rascunho anterior no editor, preservar e parar).
7. Sob `operation_lock(db_path())`, conferir janela e limite diário e reservar com `messages.reserve(...)` **antes do clique**.
8. **Clicar uma única vez** em Enviar.
9. Reabrir a conversa; confirmar texto exato, remetente Manoel e identificador do evento.
10. `messages.confirm_delivery(...)` só com a evidência. Editor esvaziar não confirma envio; confirmação ≠ leitura.

## 8. Limites e falhas
Dias úteis, **8h–18h (São Paulo)**, máx. **15 tentativas/dia** globais, pausas de **45–140 s**. Tentativas `started`, `confirmed` e `uncertain` contam no limite, que não renova a cada execução.

Falha após a reserva ou clique sem confirmação: registrar `uncertain` quando aplicável, preservar evidências e motivo, **parar, não reenviar**. `started` também bloqueia repetição. Nunca apagar/reinicializar registros para liberar reenvio. Parar diante de autenticação, CAPTCHA, checkpoint, aviso de limite, identidade divergente ou estado incerto.

## 9. Código
Python + SQLite, módulos em `src/linkedin_agent`. Usar Python para dados, hashes, aprovação, planejamento, pré-checagem e confirmação. **Não executar** os fluxos antigos que abrem perfil Playwright separado: `executor.login`, `_context`, `outreach`, `outreach-profiles`, `discover`, `send-messages` (como comandos de navegador), nem `outreach.inventory(...)`. Chamar helper de dados ≠ rodar rotina de navegação. `ui_delivery.py` está vinculado ao snapshot `lote-aprovado-2026-10-30.json`: conferir o código antes de usar em novos lotes.

## 10. Fluxo de expansão da rede (distinto da prioridade atual)
Pesquisar candidatos pelos critérios → registrar evidências e pontuar → lista curta → aprovação nominal do Manoel → convite **sem nota** → confirmar aceite por evidência → primeira mensagem individual. A nota de aderência não indica intenção de compra; não inventar campos; a região da busca não prova localização. Leitura/classificação de respostas, aprofundamento comercial e agendamento **não** são fluxos validados; respostas sempre passam por revisão e aprovação do Manoel.

## 11. Banco, dados e credenciais
- Banco principal: `data/agent.db`. **Só o computador de casa escreve** no banco do Drive; o notebook opera em leitura.
- Usar `operation_lock` em escritas (não coordena outros computadores). Sem transações abertas entre chamadas.
- Não copiar cookies/credenciais entre perfis; não gravar senhas nem códigos de autenticação.
- Preservar dados de clientes e contatos. Redigir na sessão, sem exigir API paga.
- Dados de contatos, banco e planos **não vão para este repositório**.

## 12. Estado em 05/11/2026 (consulta ao banco)
| Registro | Qtde |
|---|---:|
| Contatos `unverified` | 850 |
| Contatos `zero` | 152 |
| Contatos `has_history` | 1 |
| Contatos `contacted` | 37 |
| Entregas `confirmed` (`message_deliveries`) | 15 |
| Rascunhos `pending` | 28 |
| Rascunhos `sent` | 35 |

Tabelas de naturezas diferentes: os 37 `contacted` não são 37 entregas confirmadas. A aprovação dos rascunhos **31–45** (snapshot 30/10/2026) é histórica: consultar o estado atual antes de agir. O chat anterior registrou bloqueio na conexão com o Chrome; o navegador não foi retestado.

## 13. Instrução de continuidade
Assuma a operação do linkedin-agent. Leia `BROWSER_SESSION.md` e `ABORDAGEM.md` antes de agir; recupere o estado no banco e preserve o progresso. Confirme o Chrome habitual e a identidade. Continue a conferência (até 60 `unverified` por execução); só `zero` entra em lote. Organize até 15 contatos por dia útil, dos mais antigos aos mais novos; leia cada perfil, redija abertura individual com evidência real, salve como pendente e apresente nomes, evidências e textos completos. Envie somente o explicitamente aprovado, reconferindo histórico, registrando preflight e reserva, clicando uma vez e confirmando só com a mensagem reencontrada. Nunca repita `started`/`uncertain`. Respeite limites, atualize o planejamento e relate só o comprovado. Silêncio, data planejada ou aprovação antiga não autorizam novos textos.
