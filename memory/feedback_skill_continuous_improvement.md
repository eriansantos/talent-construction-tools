---
name: Skill de melhoria contínua via git — por quote
description: A cada novo quote: git pull antes de iniciar, git commit+push após criar. Não apenas por sessão — por quote.
type: feedback
---

A skill `talent-construction-quote` deve sincronizar com o repositório a cada quote individual, não apenas uma vez por sessão.

**Why:** Duas máquinas podem criar quotes ao mesmo tempo ou em sequência rápida. Se o pull for só no início da sessão, os aprendizados da outra máquina chegam tarde. Pull por quote garante que cada orçamento parte do conhecimento mais atual disponível.

**How to apply:**
- **Antes de cada novo quote** (mesmo que seja o segundo ou terceiro da sessão): executar `git pull --rebase origin main` no PROJECT_DIR
- **Após cada quote criado e confirmado no JobTread**: capturar observações do usuário, atualizar arquivos de aprendizado e executar `git commit + git push`
- Sequência por quote: `pull → intake → proposta → execução → aprendizado → push`
- Nunca pular o pull nem o push, mesmo que não haja aprendizados novos (nesse caso, o push não ocorre, mas a pergunta deve ser feita)
