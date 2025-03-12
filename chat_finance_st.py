import yfinance as yf
import openai
import json

from dotenv import load_dotenv
load_dotenv()

client = openai.Client()

def cotacao(ticker, periodo="1mo"):
  """Retorna a cotação de ações da Ibovespa"""
  ticker_obj = yf.Ticker(f"{ticker}.SA")
  hist = ticker_obj.history(period=periodo).get("Close")
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

msgs = [{"role": "user", "content": "Qual a cotação do banco banestes no último ano?"}]

response = client.chat.completions.create(
  messages=msgs,
  model="gpt-3.5-turbo-0125",
  tools=tools,
  tool_choice="auto"
)

tool_calls = response.choices[0].message.tool_calls

print(tool_calls)
if tool_calls: 
  msgs.append(response.choices[0].message)
  for tool_call in tool_calls:
    function_name = tool_call.function.name
    function_to_call = funcs[function_name]
    func_args = json.loads(tool_call.function.arguments)
    function_return = function_to_call(**func_args)

    msgs.append(({
      "tool_call_id": tool_call.id,
      "role": "tool",
      "name": function_name,
      "content": json.dumps(function_return) 
    }))

    segunda_resposta = client.chat.completions.create(
      messages=msgs,
      model="gpt-3.5-turbo-0125",
    )

    msgs.append(segunda_resposta.choices[0].message)
    print(segunda_resposta.choices[0].message.content)
