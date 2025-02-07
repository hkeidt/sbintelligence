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
                min-width: 250px !important;  /* Reduz a largura mínima */
                max-width: 250px !important;  /* Reduz a largura máxima */
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    
        valid_dates = df['Day'].dropna().dt.date.unique()
        if len(valid_dates) > 0:
            start_date, end_date = st.sidebar.date_input(
                "Select the days:",
                value=(min(valid_dates), max(valid_dates)),
                min_value=min(valid_dates),
                max_value=max(valid_dates)
            )
    
            # Filtrar o dataframe com base nas datas selecionadas
            df_filtered = df[(df['Day'].dt.date >= start_date) & (df['Day'].dt.date <= end_date)]
        else:
            df_filtered = df.copy()
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
    
        # Criar o gráfico
        fig_balance = px.line(
            df_complete,
            x='Day',
            y='Balance',
            title=f'{month_title}'
        )
    
        # Ajustar layout
        fig_balance.update_layout(
            title_x=0.5,
            title_font=dict(size=24),
            xaxis=dict(
                tickformat="%d",
                dtick="D1"
            ),
            yaxis_title_font=dict(size=16)
        )
    
        # Mostrar o gráfico no Streamlit
        st.plotly_chart(fig_balance, use_container_width=True)

    
    # 📊 Gráficos de Resultados e Categorias
    col_left, col_right = st.columns(2)
    
    with col_left:
        if 'Result' in df_filtered.columns:
            results_count = df_filtered['Result'].value_counts()
            fig_results = px.pie(
                values=results_count.values,
                names=results_count.index,
                title='Distribuição de Resultados'
            )
            st.plotly_chart(fig_results)
    
    with col_right:
        if 'Category' in df_filtered.columns:
            category_count = df_filtered['Category'].value_counts()
            fig_category = px.bar(
                x=category_count.index,
                y=category_count.values,
                title='Apostas por Categoria'
            )
            st.plotly_chart(fig_category)
    
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
