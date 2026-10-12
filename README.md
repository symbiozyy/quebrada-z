# Quebrada Z

Jogo 2D de sobrevivência por ondas (estilo CoD Zombies) numa favela do Rio. Feito para jogar no celular deitado.

**Jogar:** https://symbiozyy.github.io/quebrada-z/

O jogo inteiro está em `index.html` (um arquivo só). O progresso fica salvo no próprio navegador.

## Novidades da v26 — Hell de Janeiro

- **Campanha HELL DE JANEIRO:** JOGAR abre a tela de campanhas; dentro dela você escolhe a quebrada. A próxima quebrada só libera quando você **vence** a anterior (derrota o Observador na onda 14). Mapas que já estavam liberados no seu save continuam liberados.
- **Miniaturas da loja e do inventário:** cada item aparece sozinho num manequim cinza, com zoom na parte do corpo onde ele fica.
- **Habilidades:** as antigas melhorias saíram da loja e foram para PERSONAGEM › HABILIDADES, já no formato de árvore (os nós trancados chegam nas próximas versões). Níveis comprados antes foram mantidos.
- **Zumbis:** todos com a mesma paleta "infectada"; dois tipos novos (Choque, a partir da onda 8, e Mutante, que regenera, a partir da onda 11); zumbis elite de olho vermelho a partir da onda 7; dificuldade sobe por patamar (ondas 1–3, 4–6, 7–9, 10–13, 14+).
- **Capitão Caveira:** sprites das folhas SWAT (fase 1 SWAT verde, fase 2 SWAT PACK, fase 3 RAGE MODE), só limpas e ampliadas.
- **Som por proximidade:** cada zumbi geme mais alto e mais nítido conforme chega perto; os chefes ecoam no mapa inteiro.

## v26.1

- Cada cômodo tem o próprio fundo (favela, praça, quadra, baile, mata, Cristo, baía, Lapa, Arcos, escadaria), que troca com transição suave ao mudar de sala.
- Arma de parede pintada em plataforma (mirante, sacada) agora dá pra comprar de cima da plataforma.
- Pulo com intervalo de 0,30 s depois de pousar.
- Zumbi acerta quem fica pulando na frente dele; o golpe já armado não é cancelado pelo pulo.
- Caldo de Cana mais fraco (regeneração +35% em vez de 2x).
- Armas douradas bem mais raras e menos apelativas; dano das armas segue o preço (SMGs baratas um pouco mais fracas, metralhadoras pesadas valem o que custam).
- Zumbis no mezanino não ficam mais travados contra a parede quando o jogador está na mesma altura do outro lado.

## Novidades da v26.2
- **Seringa**: botão novo abaixo da Esquiva (tecla V no teclado). Cura 45% da vida, recarga de 7 s, comprada na loja (EQUIPAMENTO), acumula até 3.
- **Kit de Socorro consertado**: custa R$ 17.000, só revive se foi comprado, **uma vez por partida**, volta com 60% de vida e metade da munição (carregador e reserva), com invulnerabilidade curta.

## Novidades da v26.3
- **Vozes novas para todos os zumbis**: respiração, ataque e morte, cada uma com 3 variações sorteadas (sem repetir a mesma em seguida). Brutamontes (bruta e brutão) têm rugido e grunhido de dano ao levar tiro.
- Sons criados para o jogo a partir das referências do autor (nenhum trecho das referências foi usado). Tipos sem referência (grita, cuspidor, cão, civil, mutante, choque, Observador e Capitão Caveira) ganharam vozes próprias.
- Mantém o áudio por proximidade: mais perto do Marcus = mais alto e mais aberto. Chefes tocam sem atenuação e com eco.
- As vozes carregam depois do primeiro toque, sem travar a abertura do jogo.
