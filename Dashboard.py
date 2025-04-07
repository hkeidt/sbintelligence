import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go


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
def load_google_sheets(sheet_url, sheet_name=None):
    sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    
    # Se um nome de aba específico for fornecido, usamos ele para construir a URL
    if sheet_name:
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    else:
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

# Definir mapeamento de meses para abas
sheet_mapping = {
    "February/2025": "Feb2025",  # Substitua pelos nomes reais das suas abas
    "March/2025": "Mar2025",     # Substitua pelos nomes reais das suas abas
    "April/2025": "Apr2025"      # Adicionando a nova aba de Abril/2025
}

# Lista dos meses disponíveis para o seletor
available_months = list(sheet_mapping.keys())
available_months.sort()  # Ordena os meses

# Sidebar com filtros
st.sidebar.header("📊 Filters")

# Criar selectbox com o mês mais recente pré-selecionado
selected_month = st.sidebar.selectbox(
    "Select month:",
    options=available_months,
    index=len(available_months)-1  # Seleciona o último item da lista
)

# Obter o nome da aba correspondente ao mês selecionado
sheet_name = sheet_mapping.get(selected_month)

# Carregar os dados da aba selecionada
df = load_google_sheets(google_sheets_url, sheet_name)

if df is not None:
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

    # Converter o mês selecionado para datetime para filtrar os dados
    selected_date = pd.to_datetime(selected_month, format='%B/%Y')
    
    # Filtrar o dataframe para mostrar apenas dados do mês selecionado
    df_filtered = df[
        (df['Day'].dt.month == selected_date.month) & 
        (df['Day'].dt.year == selected_date.year)
    ]
        
    # Layout principal com quatro colunas
    col1, col2, col3, col4 = st.columns(4)
    
    # 💰 Saldo Total
    with col1:
       if 'Balance' in df_filtered.columns and not df_filtered['Balance'].isna().all():
           last_balance = df_filtered['Balance'].dropna().iloc[-1]  # Último valor do Balance
           st.metric(label="💰 Monthly Profit", value=f"R$ {last_balance:.2f}")
       else:
           st.metric(label="💰 Monthly Profit", value="N/A")
   
   # 📊 ROI
    with col2:
       if 'Balance' in df_filtered.columns and 'Stake' in df_filtered.columns and not df_filtered['Balance'].isna().all():
           last_balance = df_filtered['Balance'].dropna().iloc[-1]  # Último valor do Balance
           total_stakes = df_filtered['Stake'].dropna().sum()
           
           # Calcular ROI
           if total_stakes > 0:
               roi = ((last_balance) / total_stakes) * 100
               st.metric(
                   label="📊 Monthly ROI", 
                   value=f"{roi:.1f}%"
               )
           else:
               st.metric(label="📊 Monthly ROI", value="N/A")
       else:
           st.metric(label="📊 Monthly ROI", value="N/A")
   
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
               label="📈 Monthly Win Rate",
               value=f"{win_rate:.1f}%",
               
           )
       else:
           st.metric(label="📈 Monthly Win Rate", value="N/A")
   
   # 🎯 Odds Média
    with col4:
       if 'Odds' in df_filtered.columns and not df_filtered['Odds'].isna().all():
           avg_odds = df_filtered['Odds'].dropna().mean()
           st.metric(label="🎯 Monthly Avg Odds", value=f"{avg_odds:.2f}")
       else:
           st.metric(label="🎯 Monthly Avg Odds", value="N/A")
    
    # O resto do código permanece inalterado
    # 📈 Evolução do Saldo
    if 'Balance' in df_filtered.columns and not df_filtered['Balance'].isna().all():
    
    # Criar layout de duas colunas para os gráficos
        col_balance, col_market = st.columns([2, 1])
        
        # Na parte do gráfico, modifique esta seção:
        with col_balance:
            # Create a copy and remove NaNs
            df_graph = df_filtered.dropna(subset=['Day', 'Balance']).copy()
            
            # Create month column
            df_graph['Month'] = df_graph['Day'].dt.strftime('%B')
            
            # Get month name for title
            unique_months = df_graph['Month'].unique()
            month_title = unique_months[0] if len(unique_months) == 1 else "Multiple Months"
        
            # Get the last Balance recorded per day
            df_last_balance = df_graph.groupby(df_graph['Day'].dt.date).agg({
                'Balance': 'last',
                'Stake': 'sum',  # Soma das stakes do dia
                'Results': lambda x: list(x)  # Lista de resultados do dia
            }).reset_index()
            
            df_last_balance['Day'] = pd.to_datetime(df_last_balance['Day'])
            
            # Calculate daily profit
            df_last_balance['Daily_Profit'] = df_last_balance.apply(lambda row: 
                row['Balance'] - df_last_balance.loc[
                    df_last_balance.index < row.name, 'Balance'
                ].iloc[-1] if row.name > 0 else row['Balance'],
                axis=1
            )
            
            # Pegue o último dia com aposta para limitar a spline
            last_day_with_bet = df_last_balance['Day'].max()
            
            # Create complete date range para todo o mês
            first_day = df_last_balance['Day'].min().replace(day=1)
            last_day = df_last_balance['Day'].max().replace(day=28) + pd.DateOffset(days=4)
            last_day = last_day - pd.DateOffset(days=last_day.day)
            full_date_range = pd.date_range(start=first_day, end=last_day, freq='D')
            
            # Create complete DataFrame com todos os dias do mês
            df_complete = pd.DataFrame({'Day': full_date_range})
            
            # Fazer o merge mantendo todos os dias e preenchendo valores ausentes
            df_complete = df_complete.merge(df_last_balance, on='Day', how='left')
            
            # Forward fill para a coluna Balance (propagar o último valor conhecido)
            df_complete['Balance'] = df_complete['Balance'].fillna(method='ffill')
            
            # Para Daily_Profit, dias sem apostas ficam como zero
            df_complete['Daily_Profit'] = df_complete['Daily_Profit'].fillna(0)
            
            # Criar dataframe separado para a linha de saldo (apenas até o último dia com aposta)
            df_balance_line = df_complete[df_complete['Day'] <= last_day_with_bet].copy()
            
            # Create the figure
            fig_balance = go.Figure()
            
            # Add daily profit/loss bars para todos os dias
            fig_balance.add_trace(
                go.Bar(
                    x=df_complete['Day'],
                    y=df_complete['Daily_Profit'],
                    name='Daily P/L',
                    marker_color=df_complete['Daily_Profit'].apply(
                        lambda x: '#51cf66' if pd.notnull(x) and x > 0 else 
                                 '#ff6b6b' if pd.notnull(x) and x < 0 else 
                                 'rgba(0,0,0,0)'
                    ),
                    opacity=0.7,
                    hovertemplate='<b>Daily P/L</b>: %{y:.2f}<extra></extra>'
                )
            )
            
            # Add spline curve for cumulative balance (apenas até o último dia com aposta)
            fig_balance.add_trace(
                go.Scatter(
                    x=df_balance_line['Day'],
                    y=df_balance_line['Balance'],
                    name='Balance',
                    line=dict(shape='spline', smoothing=0.3, width=3, color='#1f77b4'),
                    mode='lines',
                    hovertemplate='<b>Balance</b>: %{y:.2f}<extra></extra>'
                )
            )
            
            # Update layout
            fig_balance.update_layout(
                title=dict(
                    text=f'{month_title}',
                    x=0.5,
                    font=dict(size=24)
                ),
                xaxis=dict(
                    tickformat="%d",
                    dtick="D1",
                    title='Day',
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.1)',
                    gridwidth=1
                ),
                yaxis=dict(
                    title='Balance / Daily P&L',
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.1)',
                    gridwidth=1,
                    range=[
                        min(
                            0, 
                            df_complete['Daily_Profit'].min() * 1.1 if not pd.isna(df_complete['Daily_Profit'].min()) else 0
                        ),
                        max(
                            df_complete['Balance'].max() * 1.1 if not pd.isna(df_complete['Balance'].max()) else 0,
                            df_complete['Daily_Profit'].max() * 1.1 if not pd.isna(df_complete['Daily_Profit'].max()) else 0
                        )
                    ]
                ),
                height=600,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            # Show the chart
            st.plotly_chart(fig_balance, use_container_width=True)
            
            
            
            
        # O restante do código permanece o mesmo...
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
            
            # Adicionar CSS para centralizar colunas
            st.markdown("""
                <style>
                div[data-testid="stDataFrame"] td {
                    text-align: center !important;
                }
                div[data-testid="stDataFrame"] th {
                    text-align: center !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            
            st.markdown("""
                <h4 style='text-align: center; color: white;'>Detailed Profit by Market</h4>
            """, unsafe_allow_html=True)
            
            # Formatar os valores da tabela
            df_table = df_profits.copy()
            
            def calculate_roi(df_table, df_profits, df):
                markets = ['1X2', 'Under', 'Over']
                
                for market in markets:
                    profits = df_profits[df_profits['Market'] == market]['Profit'].sum()
                    stakes = pd.to_numeric(df[df['Market'] == market]['Stake'], errors='coerce').sum()
                    df_table.loc[df_table['Market'] == market, 'ROI'] = 100 * (profits / stakes)
                
                ah_profits = df_profits[df_profits['Market'] == 'AH']['Profit'].sum()
                ah_stakes = pd.to_numeric(df[df['Market'] == 'AH']['Stake'], errors='coerce').sum()
                df_table.loc[df_table['Market'] == 'AH', 'ROI'] = 100 * (ah_profits / ah_stakes)
                
                return df_table
            
            # Calcular ROI
            df_table = calculate_roi(df_table, df_profits, df)
            
            # Formatar os valores
            df_table['Profit'] = df_table['Profit'].apply(lambda x: f"{float(x):,.2f}")
            df_table['ROI'] = df_table['ROI'].apply(lambda x: f"{x:.2f}%")
            
            # Remover a coluna AbsProfit se existir
            if 'AbsProfit' in df_table.columns:
                df_table = df_table.drop('AbsProfit', axis=1)
            
            # Criar uma função de estilo para centralizar todas as colunas
            def style_df(df):
                return df.style.set_properties(**{
                    'text-align': 'center',
                    'font-size': '1rem',
                    'padding': '0.5rem'
                }).set_table_styles([
                    {'selector': 'th', 'props': [('text-align', 'center')]},
                    {'selector': 'td', 'props': [('text-align', 'center')]}
                ])
            
            # Aplicar o estilo e mostrar a tabela
            styled_df = style_df(df_table.set_index('Market'))
            
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=False
            )
            
            
            
               
    
    
    # Substitua a seção do Betting Details por este código

    # 📋 Tabela de Detalhamento de Apostas
    st.markdown("""
        <style>
        /* Remove espaço extra após o gráfico */
        [data-testid="stMetric"] {
            margin-bottom: 1rem;
        }
        
        /* Ajusta o espaçamento do título da seção */
        .section-title {
            margin-top: 2rem !important;
            margin-bottom: 1rem !important;
            padding-top: 1rem !important;
            padding-bottom: 0.5rem !important;
        }
        
        /* Controla espaço da tabela */
        div[data-testid="stDataFrame"] {
            padding-top: 0.5rem !important;
        }
        
        /* Centraliza o conteúdo das células */
        div[data-testid="stDataFrame"] td {
            text-align: center !important;
        }
        div[data-testid="stDataFrame"] th {
            text-align: center !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2 class="section-title">📋 Betting Details</h2>', unsafe_allow_html=True)
    
    # Selecionar colunas da B à M (índices 1 a 12)
    df_detailed = df.iloc[:, 1:13]
    
    df_detailed['Day'] = pd.to_datetime(df_detailed['Day']).dt.strftime('%d/%m')
    
    # Converter as colunas "Balance", "Stake" e "Odds" para float
    df_detailed['Balance'] = df_detailed['Balance'].astype(float)
    df_detailed['Stake'] = df_detailed['Stake'].astype(float)
    df_detailed['Odds'] = df_detailed['Odds'].astype(float)
    
    # Arredondar as colunas
    df_detailed['Balance'] = df_detailed['Balance'].round(2)
    df_detailed['Stake'] = df_detailed['Stake'].round(2)
    df_detailed['Odds'] = df_detailed['Odds'].round(3)
    
    # Funções para formatação
    def format_two_decimals(value):
        return f"{value:.2f}"
    def format_three_decimals(value):
        return f"{value:.3f}"
    
    # Aplicar formatação
    df_detailed['Balance'] = df_detailed['Balance'].apply(format_two_decimals)
    df_detailed['Stake'] = df_detailed['Stake'].apply(format_two_decimals)
    df_detailed['Odds'] = df_detailed['Odds'].apply(format_three_decimals)
    
    # Ordenar o DataFrame
    df_detailed = df_detailed.iloc[::-1]
    
    def highlight_result(row):
        color_map = {
            'Red': 'color: #FF4C4C; font-weight: bold;',
            'Red/void': 'color: #FF9999; font-weight: bold;',
            'Void': 'color: #FFD700; font-weight: bold;',
            'Green/void': 'color: #90EE90; font-weight: bold;',
            'Green': 'color: #008000; font-weight: bold;'
        }
    
        result_column = [col for col in row.index if col.lower() in ['results', 'resultado']]
        styles = [''] * len(row)
    
        if result_column:
            col_index = row.index.get_loc(result_column[0])
            result_value = row[result_column[0]]
    
            if result_value in color_map:
                styles[col_index] = color_map[result_value]
    
        return styles
    
    # Mostrar a tabela com o novo espaçamento
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
