# Author: Wellington Braga
# created in February 2025

import openai
from colorama import Fore, Style, init
from dotenv import load_dotenv
load_dotenv()



client = openai.Client()
init(autoreset=True)
def geracao_texto(mensagens):
  """Gera respostas da API OpenAI via streaming, atualizando e imprimindo o histórico da conversa.
  Args:
  mensagens (list): Lista de dicionários com:
  Returns:
  mensagens (list): Lista atualizada com a resposta gerada.
  
  """
  resposta = client.chat.completions.create(
    messages=mensagens,
    model="gpt-3.5-turbo-0125", 
    max_tokens=1000,
    temperature=0,
    stream=True
  )

  print(f"{Fore.BLUE}Bot:", end="")

  texto_completo = ""
  for resposta_stream in resposta:
    texto = resposta_stream.choices[0].delta.content
    if texto:
      print(texto, end="")
      texto_completo += texto
  print()

  mensagens.append({"role": "assistant", "content": texto_completo})
  return mensagens

if __name__ == "__main__":
  """Bloco principal que inicializa o chatbot. 
  Exibe uma mensagem de boas-vindas, inicia a lista de mensagens e 
  entra em um loop infinito onde recebe entradas do usuário, 
  adiciona ao histórico e gera respostas usando a função geracao_texto().
"""
  print(f"{Fore.YELLOW}Bem Vindo ao Chatbot")
  mensagens = []
  while True:
    in_user = input(f"{Fore.GREEN}User: {Style.RESET_ALL}")
    mensagens.append({"role": "user", "content": in_user})
    mensagens = geracao_texto(mensagens)