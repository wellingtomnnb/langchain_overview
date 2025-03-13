import yfinance as yf
import streamlit as st
import openai
import json

from dotenv import load_dotenv
load_dotenv()

client = openai.Client()

def cotacao(ticker, periodo="1mo"):
  """Retorna a cotação de ações da Ibovespa"""
  ticker_obj = yf.Ticker(f"{ticker}.SA")
  hist = ticker_obj.history(period=periodo).get("Close")
  if len(hist) > 0:
    hist.index = hist.index.strftime("%Y-%m-%d")
    hist = round(hist, 2)
  if len(hist) > 30:
    slice_size = int(len(hist)/30)
    hist = hist.iloc[:: - slice_size][::-1]

  return hist.to_dict()

tools = [dict(
  type="function",
  function=dict(
    name="cotacao",
    description="Retorna a cotação de ações da Ibovespa",
    parameters=dict(
      type="object",
      properties=dict(
        ticker=dict(
          type="string",
          description="O ticker da ação. Ex: BBAS3, BBDC4, etc"
        ),
        periodo=dict(
          type="string",
          description="Período retornado dos dados históricos da cotação sendo:\
            '1d': 1 dia, '1mo': 1 mês, '1y': 1 ano e 'ytd': todo período",
          enum=["1d", "7d", "1mo", "6mo", "1y", "5y", "10y", "ytd", "max"]
        ),
      )
    )
  )
)]

funcs = {"cotacao": cotacao}

def gera_texto(mensagens):
    response = client.chat.completions.create(
        messages=mensagens,
        model="gpt-3.5-turbo-0125",
        tools=tools,
        tool_choice="auto"
    )

    tool_calls = response.choices[0].message.tool_calls

    if tool_calls:
        mensagens.append(response.choices[0].message)  # Adiciona a resposta do modelo
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = funcs[function_name]
            func_args = json.loads(tool_call.function.arguments)
            function_return = function_to_call(**func_args)

            # Adiciona a resposta da ferramenta corretamente
            mensagens.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(function_return)
            })

        # Faz uma segunda chamada para obter a resposta final do modelo
        segunda_resposta = client.chat.completions.create(
            messages=mensagens,
            model="gpt-3.5-turbo-0125",
        )

        mensagens.append(segunda_resposta.choices[0].message)

    return mensagens
st.set_page_config(page_title="Chatbot Financeiro", page_icon="🤖")

st.title("Chatbots de Cotação de Ações")

if "mensagens" not in st.session_state: st.session_state.mensagens = []

# Histórico de Mensagens
for msg in st.session_state.mensagens:

  # Converte para dict, caso não seja
  if not isinstance(msg, dict): msg = vars(msg)
  
  # Verifica se a mensagem possui conteúdo
  if msg["content"]:
    content = msg["content"].replace("\n", " ") # Remove quebras de linha

    if msg["role"] == "user": st.chat_message("user").markdown(content)
    if msg["role"] == "assistant": st.chat_message("assistant").markdown(content)

# Entrada de mensagem do Usuário
user_input = st.chat_input("Digite sua pergunta sobre cotação de ações")
if user_input:
  # Adicionar mensagem ao histórico
  st.session_state.mensagens.append({"role": "user", "content": user_input})
  st.chat_message("user").markdown(user_input)

  # Processar mensagem
  st.session_state.mensagens = gera_texto(st.session_state.mensagens)

  # Exibe a resposta do chatbot
  ultima_msg = st.session_state.mensagens[-1]
  
  # Converte para dict, caso não seja
  if not isinstance(ultima_msg, dict): ultima_msg = vars(ultima_msg)
  
  role = ultima_msg["role"]
  content = ultima_msg["content"]
  
  if role == "assistant": st.chat_message("assistant").markdown(content)
