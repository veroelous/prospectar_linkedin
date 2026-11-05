# Roteiro: conferir histórico e ler perfis (Chrome habitual do Manoel)

Regra geral: **em dúvida, manter `unverified`.** Nada aqui envia mensagem. Envio só com aprovação explícita (manual, seção 7).

## A. Antes de começar (toda execução)
1. Abrir o Chrome habitual (perfil do Manoel). Não usar perfil Playwright separado nem copiar cookies.
2. Confirmar na interface a conta **Manoel Gonçalves**, perfil `/in/omanoelgoncalves/`. Divergiu → parar.
3. Parar diante de login, CAPTCHA, checkpoint ou aviso de limite do LinkedIn.
4. Listar o lote da execução (até 60, mais antigos primeiro):
   ```bash
   PYTHONPATH=src python3 -m linkedin_agent.cli verify-list
   ```

## B. Conferir histórico (por contato)
1. Abrir o perfil pelo `profile_url` e confirmar que nome e foto batem com o registro.
2. Abrir a conversa com a pessoa (Mensagens → buscar o nome, ou botão *Mensagem* no perfil). Conferir nome e identificador do destinatário.
3. **Aguardar o carregamento real** do histórico (sem spinner, sem placeholder).
4. Se estiver vazia, **recarregar a página/reabrir a conversa** e olhar de novo. Tela vazia ≠ `zero`.
5. Decidir:
   | O que se vê | Estado | Evidência a registrar |
   |---|---|---|
   | Nenhuma mensagem, nem recebida, após reabrir | `zero` | "conversa reaberta; 0 eventos; AAAA-MM-DD" |
   | Qualquer mensagem (inclusive só recebida) | `has_history` | "N eventos; mais recente em ..." |
   | Já abordado antes pelo Manoel | `contacted` | origem da informação |
   | Não carregou, identidade duvidosa, erro | manter `unverified` | não registrar |
6. Registrar:
   ```bash
   PYTHONPATH=src python3 -m linkedin_agent.cli record-history ID zero "conversa reaberta; 0 eventos; 2026-11-05"
   ```
   "Zero" não prova ausência de contato em outros canais.

## C. Ler o perfil de quem ficou `zero`
1. Abrir o perfil atual e copiar, **literalmente**, o que for útil: nome, cargo/atividade, empresa e **um detalhe profissional real** (sobre/experiência/título).
2. Opcional: uma publicação recente, só se acessível e pertinente. Não citar o que não foi lido.
3. Guardar o texto do perfil lido para servir de prova do trecho usado.

## D. Redigir e salvar rascunho (pendente)
1. Estrutura: saudação pelo nome → abertura ligada ao detalhe real → conteúdo do Manoel (faturando mais e ficando mais frágil) → **uma** pergunta pedindo permissão.
2. Proibido: link, convite para reunião, oferta, presumir problema/interesse, elogio inventado, "nunca conversamos", mencionar Genoma Consultoria.
3. Salvar (o trecho de evidência precisa existir no texto do perfil informado):
   ```bash
   PYTHONPATH=src python3 -m linkedin_agent.cli save-draft ID "mensagem" "trecho do perfil" caminho/perfil.txt
   ```
   Fica `pending`. Reprovado pelo validador → corrigir, não contornar.

## E. Apresentar ao Manoel
```bash
PYTHONPATH=src python3 -m linkedin_agent.cli export-plan
```
Mostrar, por pessoa: nome/perfil, contexto, personalização, **mensagem integral**, ID do rascunho, situação. A IA não aprova. A aprovação vale para destinatário e texto exatos; qualquer alteração exige nova aprovação.

## F. Encerrar a execução
Registrar o que foi conferido, o que ficou `unverified` e o motivo, e eventuais bloqueios. Relatar só o comprovado.
