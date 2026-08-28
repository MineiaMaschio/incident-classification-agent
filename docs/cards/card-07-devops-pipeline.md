# 🚀 Card 07: DevOps Pipeline — CI/CD Automatizado

**Branch:** `feature/devops-pipeline`  
**Objetivo:** Configurar pipeline de integração contínua com lint, testes e validação de configuração, garantindo que cada push ao repositório passe por verificação automatizada.

---

## 📌 Escopo

### Pipeline

- [x] Criar `.github/workflows/ci.yml` com as etapas:
  - [x] **lint** — verificação de estilo e qualidade de código (ruff)
  - [x] **test** — execução do pytest com os testes do Card 06
  - [x] **validate-config** — verificar que `.env.example` existe e contém as chaves `OLLAMA_MODEL` e `RESIDENTS_API_URL`

### Ferramentas

- [x] Adicionar `ruff` ao grupo `dev` do `pyproject.toml`
- [x] Configurar regras de lint no `pyproject.toml`

### Documentação

- [x] Documentar o pipeline em `docs/devops/pipeline.md`: etapas, o que cada uma verifica e como interpretar falhas

---

## 🏁 Resultado Esperado

- [x] Pipeline executa em todo push e pull request
- [x] Lint, testes e validação de config passando
- [x] Documentação do pipeline criada

---

## 📎 Referências

- `pyproject.toml`
- `tests/`
- `docs/devops/`

---

## ✅ Implementação Concluída

### Arquivos Criados/Modificados

1. **pyproject.toml**
   - Adicionado `ruff>=0.8.0` ao grupo `dev`
   - Configuradas regras ruff: line-length=100, target-version=py312, select E/W/F/I, ignore E501
   - Exclusões: tests, .venv, __pycache__, .pytest_cache

2. **.github/workflows/ci.yml**
   - Job **lint**: ruff check em src/, tests/, api/
   - Job **test**: pytest com -v --tb=short
   - Job **validate-config**: verifica .env.example e presença de OLLAMA_MODEL e RESIDENTS_API_URL
   - Triggers: push em main/develop/feature/*/bugfix/*, pull_request em main/develop

3. **docs/devops/pipeline.md**
   - Documentação completa do pipeline (3 etapas)
   - O que cada etapa verifica
   - Como interpretar falhas
   - Comandos para replicar localmente
   - Troubleshooting e best practices

### Status

- ✅ Pipeline configurado e pronto para uso
- ✅ Ruff instalado como dependência dev
- ✅ Documentação completa
- ✅ Validações de config implementadas
