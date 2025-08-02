# Análise de Dados de Corridas da Uber

Este projeto destina-se à análise de dados de corridas da Uber, seguindo o desafio técnico descrito em [`docs/PROJECT DOCUMENTATION.md`](docs/PROJECT%20DOCUMENTATION.md). O objetivo é realizar a ingestão, limpeza, transformação e análise de um dataset público para extrair insights valiosos.

##  Estrutura do Projeto

O projeto está organizado da seguinte forma:

```
uber_analisys/
├── app/               # Contém o código-fonte da aplicação
├── data/              # Armazena os datasets brutos e processados
├── docs/              # Documentação do projeto
├── tests/             # Testes unitários e de integração
├── pyproject.toml     # Arquivo de configuração do projeto e dependências
└── Readme.md          # Este arquivo
```

## Configuração do Ambiente

Siga os passos abaixo para configurar o ambiente de desenvolvimento local.

### Pré-requisitos

- Python 3.9+
- Poetry (para gerenciamento de dependências)
- Git

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/JpedroCSantos/uber_analisys.git
    cd uber_analisys
    ```

2.  **Instale as dependências:**
    O projeto utiliza [Poetry](https://python-poetry.org/) para gerenciar as dependências. Para instalá-las, execute:
    ```bash
    poetry install
    ```

3.  **Ative o ambiente virtual:**
    ```bash
    poetry shell
    ``` 