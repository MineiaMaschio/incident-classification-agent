# 🚀 PROMPT CARD 07: DevOps Pipeline — CI/CD Automatizado

## 🎯 Objetivo

Implementar um pipeline de CI/CD com GitHub Actions que execute lint, testes e validação de configuração em cada push e pull request.

---

## 📋 Tarefas

### 1. Adicionar `ruff` ao `pyproject.toml`

Adicionar `ruff>=0.8.0` ao grupo `dev` e configurar:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I"]
ignore = ["E501"]
exclude = ["tests", ".venv", "__pycache__", ".pytest_cache"]
```

---

### 2. Criar `.github/workflows/ci.yml`

Pipeline com 3 jobs:

**lint:**
- Setup Python 3.12
- Instalar ruff
- Executar `ruff check src/ tests/ api/`

**test:**
- Setup Python 3.12
- Instalar `pip install -e ".[dev]"`
- Executar `python -m pytest tests/ -v --tb=short`

**validate-config:**
- Verificar `.env.example` existe
- Verificar `OLLAMA_MODEL` em `.env.example`
- Verificar `RESIDENTS_API_URL` em `.env.example`

Trigger: push em main/develop/feature/*/bugfix/*, pull_request em main/develop

---

### 3. Documentar em `docs/devops/pipeline.md`

Descrever:
- Etapas do pipeline (lint, test, validate-config)
- O que cada uma verifica
- Como interpretar falhas
- Comandos para replicar localmente

---

## ✅ Validação

- Lint passa sem violações
- Testes: 79 passed, 1 skipped
- Config: OLLAMA_MODEL e RESIDENTS_API_URL encontrados
- Pipeline verde no GitHub
