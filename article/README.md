# Artigo Cientifico TokLang — Padrao SBC (Sociedade Brasileira de Computacao)

Este diretorio contem a versao preliminar e a estrutura completa do artigo cientifico derivado da monografia de Conclusao de Curso (TCC II) em Ciencia da Computacao pelo Centro Universitario Max Planck (UniMAX).

---

## 1. Identificacao do Manuscrito

- **Titulo:** TokLang: Uma Linguagem de Programacao Orientada a Tokens para Compilacao, Otimizacao e Retencao Semantica em Modelos de Linguagem de Grande Porte
- **Title (English):** TokLang: A Token-Oriented Programming Language for Compilation, Optimization, and Semantic Retention in Large Language Models
- **Area de Concentracao:** Engenharia de Software, Linguagens de Programacao e Inteligencia Artificial
- **Publico-Alvo / Forum:** Eventos da SBC (ex: CSBC / WEI / SBES / EnIAC) ou periodicado correlato

## 2. Autoria e Filiacao Institucional

1. **Matheus Sousa dos Santos** (RA: 52319400) — `52319400@unimax.edu.br`
2. **Felipe Guarnieri Pinete** (RA: 52319337) — `52319337@unimax.edu.br`
3. **Guilherme Gustavo Weber** (RA: 52420339) — `52420339@unimax.edu.br`
4. **Juan Pedro** (RA: 52319411) — `52319411@unimax.edu.br`
5. **Prof. Me. Luiz Claudio Chiavini** (Orientador) — `luiz.chiavini@unimax.edu.br`

**Instituicao:**  
Centro Universitario Max Planck (UniMAX) — Grupo Educlever  
Colegiado de Ciencia da Computacao  
Indaiatuba, SP, Brasil

---

## 3. Estrutura dos Arquivos

- `artigo_toklang_sbc.md`: Texto integral do artigo em Markdown formatado segundo as normas de publicacao da SBC (estrutura de 10 a 12 paginas equivalentes).
- `referencias_sbc.bib`: Arquivo BibTeX compilado contendo todas as referencias bibliograficas com links, DOIs e chaves de citacao canonicas.
- `/figures`: As figuras referenciadas no artigo estao geradas e mantidas no diretorio raiz `../figures/` em resolucao vetorial (300 DPI).

---

## 4. Instrucoes de Compilacao para LaTeX (SBC Template)

Para compilar o artigo para o template oficial `sbc-template.tex`:
1. Baixe o pacote oficial da SBC: `sbc-template.zip` (disponivel no portal da SBC).
2. Utilize a estrutura de secoes e paragrafos contida em `artigo_toklang_sbc.md`.
3. Copie o arquivo `referencias_sbc.bib` para o diretorio de build do LaTeX.
4. Compile via `pdflatex artigo_toklang_sbc.tex && bibtex artigo_toklang_sbc && pdflatex artigo_toklang_sbc.tex`.
