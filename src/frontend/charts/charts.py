import plotly.express as px


def grafico_evolucao(df, categoria):
    fig = px.line(df, x="data", y="valor", title=f"Evolução da categoria {categoria}")
    return fig
