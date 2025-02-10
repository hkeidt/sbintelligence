import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração do Streamlit
st.set_page_config(page_title='Dashboard de Apostas', layout='wide')
st.title('🎲 SBIntelligence - Dashboard Profit')

# Função para converter strings numéricas para float
def convert_to_float(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.replace('R$', '').replace(' ', '').replace(',', '.')
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# Função para carregar dados do Google Sheets
def load_google_sheets(sheet_url):
    sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    
    try:
        df = pd.read_csv(csv_url)
        
        # Converter colunas numéricas
        numeric_columns = ['Balance', 'Odds', 'Stake']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(convert_to_float)
        
        # Converter a coluna Day para datetime
        if 'Day' in df.columns:
            try:
                df['Day'] = pd.to_datetime(df['Day'], format='%d/%m', errors='coerce')
                df['Day'] = df['Day'].apply(lambda x: x.replace(year=2025) if pd.notnull(x) else x)
                df = df.dropna(subset=['Day'])
            except Exception as e:
                st.warning(f"Aviso: Erro ao converter datas: {e}")
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        return None

# URL da planilha do Google Sheets
google_sheets_url = "https://docs.google.com/spreadsheets/d/1fe_WjUo_8F68a0nOUZQjFCPbP0k7C2EkgkM-tjCFwD0/edit"

# Carregar os dados
df = load_google_sheets(google_sheets_url)

if df is not None:
    # Sidebar com filtros
    st.sidebar.header("📊 Filters")
    
    # Filtro de data
    if 'Day' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Day']):
        
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] {
                min-width: 250px !important;
                max-width: 250px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    
        # Criar lista de meses/anos disponíveis no formato "Month/Year"
        available_months = sorted(df['Day'].dt.strftime('%B/%Y').unique())
        
        # Pegar o último mês da lista (mais recente)
        latest_month = available_months[-1]
        
        # Criar selectbox com o mês mais recente pré-selecionado
        selected_month = st.sidebar.selectbox(
            "Select month:",
            options=available_months,
            index=len(available_months)-1  # Seleciona o último item da lista
        )
        
        # Converter o mês selecionado para datetime
        selected_date = pd.to_datetime(selected_month, format='%B/%Y')
        
        # Filtrar o dataframe para mostrar apenas dados do mês selecionado
        df_filtered = df[
            (df['Day'].dt.month == selected_date.month) & 
            (df['Day'].dt.year == selected_date.year)
        ]
    else:
        df_filtered = df.copy()
        
        
        
    # Layout principal com quatro colunas
    col1, col2, col3, col4 = st.columns(4)
    
    # 💰 Saldo Total
    with col1:
       if 'Balance' in df_filtered.columns and not df_filtered['Balance'].isna().all():
           last_balance = df_filtered['Balance'].dropna().iloc[-1]  # Último valor do Balance
           st.metric(label="💰 Profit", value=f"R$ {last_balance:.2f}")
       else:
           st.metric(label="💰 Profit", value="N/A")
   
   # 📊 ROI
    with col2:
       if 'Balance' in df_filtered.columns and 'Stake' in df_filtered.columns and not df_filtered['Balance'].isna().all():
           last_balance = df_filtered['Balance'].dropna().iloc[-1]  # Último valor do Balance
           total_stakes = df_filtered['Stake'].dropna().sum()
           
           # Calcular ROI
           if total_stakes > 0:
               roi = ((last_balance) / total_stakes) * 100
               st.metric(
                   label="📊 ROI", 
                   value=f"{roi:.1f}%"
               )
           else:
               st.metric(label="📊 ROI", value="N/A")
       else:
           st.metric(label="📊 ROI", value="N/A")
   
   # 📈 Taxa de Acerto
    with col3:
       if 'Results' in df_filtered.columns:
           # [Rest of the existing win rate calculation remains the same]
           total_wins = len(df_filtered[df_filtered['Results'] == 'Green'])
           total_losses = len(df_filtered[df_filtered['Results'] == 'Red'])
           total_half_win = len(df_filtered[df_filtered['Results'] == 'Green/void']) * 0.5
           total_half_loss = len(df_filtered[df_filtered['Results'] == 'Red/void']) * 0.5
           
           total_valid_bets = total_wins + total_losses + total_half_win + total_half_loss
           
           if total_valid_bets > 0:
               win_rate = ((total_wins + total_half_win) / total_valid_bets) * 100
           else:
               win_rate = 0

           st.metric(
               label="📈 Win Rate",
               value=f"{win_rate:.1f}%",
               
           )
       else:
           st.metric(label="📈 Taxa de Acerto", value="N/A")
   
   # 🎯 Odds Média
    with col4:
       if 'Odds' in df_filtered.columns and not df_filtered['Odds'].isna().all():
           avg_odds = df_filtered['Odds'].dropna().mean()
           st.metric(label="🎯 Avg Odds", value=f"{avg_odds:.2f}")
       else:
           st.metric(label="🎯 Avg Odds", value="N/A")
    
       
        # 📈 Evolução do Saldo
    if 'Balance' in df_filtered.columns and not df_filtered['Balance'].isna().all():
    
    # Criar layout de duas colunas para os gráficos
        col_balance, col_market = st.columns([2, 1])
        
        with col_balance:
            # Criar uma cópia e remover NaNs
            df_graph = df_filtered.dropna(subset=['Day', 'Balance']).copy()
            
            # Criar a coluna do mês
            df_graph['Month'] = df_graph['Day'].dt.strftime('%B')
            
            # Obter o nome do mês para o título
            unique_months = df_graph['Month'].unique()
            month_title = unique_months[0] if len(unique_months) == 1 else "Multiple Months"
        
            # Obter o último Balance registrado por dia
            df_last_balance = df_graph.groupby(df_graph['Day'].dt.date)['Balance'].last().reset_index()
            df_last_balance['Day'] = pd.to_datetime(df_last_balance['Day'])
        
            # Criar uma faixa de datas do primeiro ao último dia do mês
            first_day = df_last_balance['Day'].min().replace(day=1)
            last_day = df_last_balance['Day'].max().replace(day=28) + pd.DateOffset(days=4)
            last_day = last_day - pd.DateOffset(days=last_day.day)  # Ajusta para o último dia do mês
            full_date_range = pd.date_range(start=first_day, end=last_day, freq='D')
        
            # Criar DataFrame completo com todos os dias
            df_complete = pd.DataFrame({'Day': full_date_range})
            df_complete = df_complete.merge(df_last_balance, on='Day', how='left')
        
            # Em vez de preencher os valores ausentes, manter como NaN para quebrar a linha nos dias sem apostas
            df_complete.loc[df_complete['Balance'].isna(), 'Balance'] = None
        
            # Criar o gráfico de linha
            fig_balance = px.line(
                df_complete,
                x='Day',
                y='Balance',
                title=f'{month_title}'
            )
        
            # Ajustar layout para garantir que o Y comece em 0 e definir altura total
            fig_balance.update_layout(
                title_x=0.5,
                title_font=dict(size=24),
                xaxis=dict(
                    tickformat="%d",
                    dtick="D1"
                ),
                yaxis=dict(
                    range=[0, df_complete['Balance'].max() + 1]
                ),
                yaxis_title_font=dict(size=16),
                height=600  # Aumentada para corresponder à altura combinada do gráfico de profit (400) + espaço da tabela
            )
        
            # Mostrar o gráfico no Streamlit
            st.plotly_chart(fig_balance, use_container_width=True)
            
            
        
        with col_market:
            # Função para calcular profit por mercado
            def calculate_market_profit(df, market_type):
                market_df = df[df['Market'].str.contains(market_type, case=False, na=False)]
                
                if len(market_df) == 0:
                    return 0
                    
                market_profit = 0
                for _, bet in market_df.iterrows():
                    if bet['Results'] == 'Green':
                        market_profit += bet['Stake'] * (bet['Odds'] - 1)
                    elif bet['Results'] == 'Green/void':
                        market_profit += bet['Stake'] * (bet['Odds'] - 1) * 0.5
                    elif bet['Results'] == 'Red':
                        market_profit -= bet['Stake']
                    elif bet['Results'] == 'Red/void':
                        market_profit -= bet['Stake'] * 0.5
                
                return market_profit
            
            # Calcular profits por mercado
            profits = {
                '1X2': calculate_market_profit(df_filtered, '1X2'),
                'AH': calculate_market_profit(df_filtered, 'AH'),
                'Under': calculate_market_profit(df_filtered, 'Under'),
                'Over': calculate_market_profit(df_filtered, 'Over')
            }
            
            # Criar DataFrame para os gráficos
            df_profits = pd.DataFrame({
                'Market': profits.keys(),
                'Profit': profits.values()
            })
            
            # Ordenar por valor absoluto do profit
            df_profits = df_profits.sort_values('Profit', key=abs, ascending=True)
            
            # Criar seletor para escolher o tipo de visualização
            chart_type = st.radio(" ", 
                                 ["Bar Chart", "Pie Chart"],
                                 horizontal=True)
            
            if chart_type == "Bar Chart":
                # Criar gráfico de barras horizontais
                fig = px.bar(
                    df_profits,
                    x='Profit',
                    y='Market',
                    orientation='h',
                    title='Profit by Market'
                )
                
                # Definir cores baseadas no sinal do profit
                fig.update_traces(
                    marker_color=['#ff6b6b' if x < 0 else '#51cf66' for x in df_profits['Profit']]
                )
                
                # Ajustar layout
                fig.update_layout(
                    title=dict(
                        text='Profit by Market',
                        x=0.5,
                        y=0.95,
                        xanchor='center',
                        yanchor='top'
                    ),
                    title_font=dict(size=24),
                    showlegend=False,
                    xaxis_title="Profit",
                    yaxis_title="",
                    height=250,
                    margin=dict(b=0, t=40)
                )
                
            else:  # Gráfico de Pizza
                # Usar valor absoluto para tamanho dos segmentos
                df_profits['AbsProfit'] = abs(df_profits['Profit'])
                
                # Definir uma paleta de cores diferentes para cada mercado
                color_palette = ['#0077B6', '#00B4D8', '#48CAE4', '#90E0EF']
                
                # Criar gráfico de pizza
                fig = px.pie(
                    df_profits,
                    values='AbsProfit',
                    names='Market',
                    title='Profit by Market',
                    color='Market',  # Usar Market como base para as cores
                    color_discrete_sequence=color_palette  # Usar nossa paleta personalizada
                )
                
                # Ajustar layout
                fig.update_layout(
                    title=dict(
                        text='Profit by Market',
                        x=0.5,
                        y=0.95,
                        xanchor='center',
                        yanchor='top'
                    ),
                    title_font=dict(size=24),
                    showlegend=False,
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="right",
                        x=1.2
                    ),
                    height=250,
                    margin=dict(b=0, t=40)
                )
                
                # Ajustar o formato dos valores no hover e text
                fig.update_traces(
                    texttemplate="<b>%{label}</b><br>%{customdata[0]:.2f}",
                    customdata=df_profits[['Profit']],
                    hovertemplate="<b>%{label}</b><br>%{customdata[0]:.2f}<br>%{percent}<extra></extra>"
                )
            
            # Mostrar o gráfico selecionado
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # Inserir CSS global para controlar espaçamentos
            st.markdown("""
                <style>
                    /* Remove espaço extra após o gráfico */
                    [data-testid="stMetric"] {
                        margin-bottom: 1rem;
                    }
                    
                    /* Controla espaço do título */
                    div.stMarkdown h4 {
                        margin-top: -3rem !important;
                        padding-top: 0 !important;
                        margin-bottom: 0.5rem !important;
                    }
                    
                    /* Controla espaço da tabela */
                    div[data-testid="stDataFrame"] {
                        margin-top: -2rem !important;
                        padding-top: 0 !important;
                    }
                    
                    /* Remove padding extra dos containers */
                    .element-container {
                        padding-top: 0 !important;
                        margin-top: 0 !important;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # Inserir um espaço invisível para ajudar no posicionamento
            st.markdown('<div style="margin-top: -3rem;"></div>', unsafe_allow_html=True)
            
            st.markdown("""
                <h4 style='text-align: center; color: white;'>Detailed Profit by Market</h4>
            """, unsafe_allow_html=True)
                
            # Formatar os valores da tabela
            df_table = df_profits.copy()
            df_table['Profit'] = df_table['Profit'].apply(lambda x: f"{x:.2f}")
            
            # Mostrar tabela sem o índice e a coluna AbsProfit
            if 'AbsProfit' in df_table.columns:
                df_table = df_table.drop('AbsProfit', axis=1)
            
            # Mostrar a tabela
            st.dataframe(df_table.set_index('Market'), use_container_width=True)
                        
            
    
    
    
    
    # 📋 Tabela de Detalhamento de Apostas
    st.subheader("📋 Betting Details")
    
    # Selecionar colunas da B à M (índices 1 a 12)
    df_detailed = df.iloc[:, 1:13]
    
    df_detailed['Day'] = pd.to_datetime(df_detailed['Day']).dt.strftime('%d/%m')
    
    # Converter as colunas "Balance", "Stake" e "Odds" para float (caso ainda não sejam)
    df_detailed['Balance'] = df_detailed['Balance'].astype(float)
    df_detailed['Stake'] = df_detailed['Stake'].astype(float)
    df_detailed['Odds'] = df_detailed['Odds'].astype(float)
    
    # Arredondar as colunas para 2 casas decimais
    df_detailed['Balance'] = df_detailed['Balance'].round(2)
    df_detailed['Stake'] = df_detailed['Stake'].round(2)
    df_detailed['Odds'] = df_detailed['Odds'].round(3)
    
    # Função para formatar valores com 2 casas decimais
    def format_two_decimals(value):
        return f"{value:.2f}"
    def format_three_decimals(value):
        return f"{value:.3f}"
    
    # Aplicar a formatação às colunas "Balance", "Stake" e "Odds"
    df_detailed['Balance'] = df_detailed['Balance'].apply(format_two_decimals)
    df_detailed['Stake'] = df_detailed['Stake'].apply(format_two_decimals)
    df_detailed['Odds'] = df_detailed['Odds'].apply(format_three_decimals)

    
    # Ordenar o DataFrame pelo índice de trás para frente
    df_detailed = df_detailed.iloc[::-1]
    
    def highlight_result(row):
        # Dicionário de cores para cada resultado (aplicado ao texto)
        color_map = {
            'Red': 'color: #FF4C4C; font-weight: bold;',         # Vermelho forte
            'Red/void': 'color: #FF9999; font-weight: bold;',   # Vermelho mais claro
            'Void': 'color: #FFD700; font-weight: bold;',       # Amarelo
            'Green/void': 'color: #90EE90; font-weight: bold;', # Verde claro
            'Green': 'color: #008000; font-weight: bold;'       # Verde forte
        }
    
        # Verifica se há uma coluna de resultado
        result_column = [col for col in row.index if col.lower() in ['results', 'resultado']]
    
        # Criar uma lista vazia para armazenar os estilos
        styles = [''] * len(row)
    
        if result_column:
            col_index = row.index.get_loc(result_column[0])  # Obtém o índice da coluna "Results"
            result_value = row[result_column[0]]
    
            if result_value in color_map:
                styles[col_index] = color_map[result_value]  # Aplica o estilo apenas à célula correspondente
    
        return styles  # Retorna os estilos para cada célula da linha
    
    st.dataframe(
        df_detailed.style.apply(highlight_result, axis=1),
        use_container_width=True
    )
    
    # 📥 Download dos dados filtrados
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download dos dados",
        data=csv,
        file_name="betting_data.csv",
        mime="text/csv"
    )
else:
    st.error("⚠️ Não foi possível carregar os dados.")

st.write("Desenvolvido por SBI ⚽")
