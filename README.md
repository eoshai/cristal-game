# 💎 O Resgate do Cristal 3D

Um jogo de exploração em primeira pessoa (FPS) desenvolvido em Python utilizando a biblioteca **Ursina Engine**.

O objetivo do jogador é explorar um labirinto, encontrar três chaves perdidas, usar as chaves para abrir a jaula trancada e recuperar o cristal místico antes que o tempo se esgoste[cite: 1].

---

## 🎮 Mecânicas e Funcionalidades

- **Visão em Primeira Pessoa:** Controlos intuitivos no estilo *First-Person Controller*[cite: 1].
- **Dificuldade Progressiva:** A velocidade da contagem decrescente do tempo aumenta ligeiramente a cada chave recolhida ($+15\%$)[cite: 1].
- **Sistemas de Orientação:** Indicador visual (seta no HUD) que aponta para a chave mais próxima ou para a jaula[cite: 1].
- **Animações e Efeitos Visuais:**
  - Animação e luz ao recolher itens[cite: 1].
  - Confetes em caso de vitória[cite: 1].
  - Portão da jaula animado e cadeado decorativo[cite: 1].
- **Efeitos de Áudio Integrados:**
  - Passos ao caminhar, sons de interação e efeito para vitória/derrota[cite: 1].
  - Áudio de reserva nativo para evitar *lag* ou perdas de FPS[cite: 1].
- **Sistema de Classificação (Rank):** Desempenho pontuado (Rank S, A ou B) com base no tempo restante ao concluir o objetivo[cite: 1].

---

## ⌨️ Controlos do Jogo

| Tecla / Ação | Função |
| :--- | :--- |
| **W, A, S, D** | Movimentar o jogador[cite: 1] |
| **Mouse** | Olhar ao redor (controlo de câmara)[cite: 1] |
| **Espaço** | Saltar[cite: 1] |
| **Enter** | Iniciar o jogo (Menu) / Confirmar saída[cite: 1] |
| **R** | Reiniciar e voltar ao menu (Ecrã de Fim de Jogo)[cite: 1] |
| **ESC** | Abrir/Fechar menu de confirmação para sair[cite: 1] |

---

## 🛠️ Requisitos e Pré-requisitos

- **Python:** Versão 3.8 ou superior instalada.
- **Biblioteca Ursina Engine:**
  ```bash
  pip install ursina
  ```

---

## 📁 Estrutura de Pastas Esperada

Para que os efeitos sonoros personalizados funcionem corretamente, garanta que a estrutura de pastas está organizada da seguinte forma:

```text
meu_jogo/
│
├── main.py
└── sounds/
    ├── musica_fundo.mp3   (ou .wav / .ogg)
    ├── coletar_chave.wav
    ├── abrir_portao.wav
    ├── vitoria.wav
    ├── derrota.wav
    └── passo.wav
```

> Nota: Caso os ficheiros na pasta `sounds/` não existam, o jogo utilizará automaticamente os sons nativos de reserva da Ursina sem interromper a execução.
> 
> 

---

## 🚀 Como Executar o Jogo

1. Clone ou transfira este repositório.
2. Certifique-se de que instalou a dependência `ursina`.
3. Execute o ficheiro principal no seu terminal/prompt de comando:

```bash
python main.py

```

---

## ⚙️ Personalização Rápidas

No início do código `main.py`, na secção **Configurações Gerais**, pode ajustar variáveis simples para alterar a dificuldade:

```python
TEMPO_MAXIMO = 60                 # Tempo inicial da partida em segundos
INCREMENTO_DIFICULDADE = 0.15     # Aceleração do tempo por chave recolhida

```

```

```
