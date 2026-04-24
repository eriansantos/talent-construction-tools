# Instalação da Skill — Talent Construction Quote

Skill para criar orçamentos conversacionalmente e enviar ao JobTread via API.

**Repositório:** `https://github.com/eriansantos/talent-construction-tools`

---

## Pré-requisitos

- [Claude Code](https://claude.ai/code) instalado
- Git instalado ([mac](https://git-scm.com) / [windows](https://git-scm.com/download/win))
- Python 3.8+ instalado

---

## Instalação

### Mac

```bash
# 1. Clonar o repositório
git clone https://github.com/eriansantos/talent-construction-tools ~/Projects/talent-construction-tools

# 2. Criar a pasta de skills do Claude (se não existir)
mkdir -p ~/.claude/skills

# 3. Instalar a skill via symlink (recomendado — atualizações automáticas com git pull)
ln -s ~/Projects/talent-construction-tools/talent-construction-quote ~/.claude/skills/talent-construction-quote
```

### Windows (PowerShell como Administrador)

```powershell
# 1. Clonar o repositório
git clone https://github.com/eriansantos/talent-construction-tools "$env:USERPROFILE\Projects\talent-construction-tools"

# 2. Criar a pasta de skills do Claude (se não existir)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills"

# 3. Instalar a skill via symlink (recomendado — atualizações automáticas com git pull)
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\talent-construction-quote" -Target "$env:USERPROFILE\Projects\talent-construction-tools\talent-construction-quote"
```

> **Windows sem permissão de admin?** Use cópia em vez de symlink (ver seção abaixo).

---

## Verificar instalação

Reinicie o Claude Code. Na próxima conversa, diga:

> "cria um orçamento"

A skill deve ser ativada automaticamente e iniciar a FASE 0 (setup + sync).

---

## Atualizações

Como a skill está instalada via symlink, basta fazer `git pull` no repositório:

### Mac
```bash
cd ~/Projects/talent-construction-tools && git pull
```

### Windows (PowerShell)
```powershell
cd "$env:USERPROFILE\Projects\talent-construction-tools"; git pull
```

Nenhuma reinstalação necessária — o symlink já aponta para a versão mais recente.

---

## Instalação sem symlink (cópia simples)

Se preferir copiar em vez de usar symlink, a skill **não atualiza automaticamente** — será necessário repetir o passo de cópia após cada `git pull`.

### Mac
```bash
cp -r ~/Projects/talent-construction-tools/talent-construction-quote ~/.claude/skills/
```

### Windows (PowerShell)
```powershell
Copy-Item -Recurse -Force "$env:USERPROFILE\Projects\talent-construction-tools\talent-construction-quote" "$env:USERPROFILE\.claude\skills\talent-construction-quote"
```

---

## Desinstalar

### Mac
```bash
rm -rf ~/.claude/skills/talent-construction-quote
```

### Windows (PowerShell)
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\skills\talent-construction-quote"
```
