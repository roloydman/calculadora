# AGENTS.md — template ai-workspace

> Copie este arquivo para a raiz de cada projeto gerenciado (`<projeto>/AGENTS.md`)
> e ajuste a seção "Projeto" conforme necessário.

## Idioma (regra obrigatória)

- O usuário escreve em **Português (PT-BR)**. Responda a ele em PT-BR.
- Gere **SEMPRE em Inglês (EN)**: código, nomes de variáveis/funções,
  comentários de código, mensagens de commit e nomes de arquivos.

## Memória Compartilhada (ai-memory)

- Este projeto utiliza o `ai-memory` local.
- Antes de iniciar qualquer tarefa complexa ou arquitetural, use `memory_query` para consultar decisões passadas e lições aprendidas.
- Ao concluir uma implementação ou decisão importante, registre o aprendizado usando `memory_write_page`.
- O desenvolvedor instruirá em Português (PT-BR). Responda e gere código, variáveis e commits estritamente em Inglês.
- Use por padrão os modelos gratuitos configurados no OpenCode.

## Projeto

- Diretório: <preencher>
- Agente default: `opencode` (modelo free, ex.: `opencode/deepseek-v4-flash-free`)
- Comandos de verificação: <ex.: `cargo test`, `npm test`, `pytest`>
