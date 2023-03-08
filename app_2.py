import streamlit as st 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3

df = pd.read_csv('data/data.csv')

def data_transform(data):
	meses = {
    'enero': 'January',
    'febrero': 'February',
    'marzo': 'March',
    'abril': 'April',
    'mayo': 'May',
    'junio': 'June',
    'julio': 'July',
    'agosto': 'August',
    'septiembre': 'September',
    'octubre': 'October',
    'noviembre': 'November',
    'diciembre': 'December'}
	data['Fecha_Update'] = data['Fecha_Update'].apply(lambda x :x.split(',')[1].strip())
	data['Fecha_Update'] = data['Fecha_Update'].replace(meses, regex=True)
	data['Fecha_Update'] = pd.to_datetime(data['Fecha_Update'] , format='%d de %B de %Y')
	data['Day'] = data['Fecha_Update'].dt.day_name()
	data.loc[(data.Estatus.isnull())&(data.TXN>0),'Estatus'] = 'TRANSACTION'
	data.loc[(data.Estatus.isnull())&(data.TXN==0),'Estatus'] = 'NO_RESPONSE'
	
	return data

def graph_cum(data):
	data_grouped_month = data.loc[(data.Estatus== 'APPROVED'),:].groupby(pd.Grouper(key='Fecha_Update', freq='M'))['Numero_cliente'].count().reset_index()
	data_grouped_month['conteo_acumulativo'] = data_grouped_month['Numero_cliente'].cumsum()
	
	fig, ax = plt.subplots(figsize=(10, 6))
	sns.lineplot(x='Fecha_Update', y='conteo_acumulativo', data=data_grouped_month, linewidth=2.5, color='blue', ax=ax)
	ax.set_title('Users with credit card', fontsize=12)
	ax.set_xlabel('Fecha', fontsize=14)
	ax.set_ylabel('Valor', fontsize=14)
	ax.legend(['Cummulative count'], loc='upper left', fontsize=12)

	return fig 

def graph_pie(data):
	data_grouped_motivo = data.loc[(df.Estatus== 'APPROVED'),:].groupby('Motivo')['Numero_cliente'].count().reset_index()
	fig, ax = plt.subplots(figsize=(10, 6))
	ax.pie(data_grouped_motivo['Numero_cliente'], labels=data_grouped_motivo['Motivo'], autopct='%1.1f%%', startangle=90)
	ax.axis('equal')
	plt.title('Credit card Type', fontsize=12)

	return fig 

def graph_bar_c(data):
	data = pd.DataFrame(pd.pivot_table(data.loc[df.Estatus.isin(['RESPONSE','NO_RESPONSE'])], values = 'Id_product',index='Estatus', columns='canal_venta', aggfunc='count', margins = True))
	data.reset_index(inplace = True)
	ind = np.arange(2)
	width = 0.09
	fig = plt.figure(figsize=(10,6)); ax = plt.axes()
	ax.bar(ind+ 0.00, data.Marketing[0:2].values, width, color='r') # barra roja. 
	ax.bar(ind+ 0.15, data.Operaciones[0:2].values, width, color='b') # barra azul 
	ax.bar(ind+ 0.30, data['Servicio al cliente'][0:2].values, width, color='g') # barra azul 
	ax.set_ylabel('Clients'); 
	ax.set_title('Conversion')
	ax.set_xticks(ind)
	ax.set_xticklabels(['NO_RESPONSE', 'RESPONSE'])
	ax.legend(labels=['Marketing', 'Operaciones', 'Servicio al cliente'])

	return fig 

def graph_den(data):
	fig = plt.figure(figsize=(10,6))
	sns.set_style('whitegrid')
	sns.kdeplot(data=data.loc[(data.Estatus== 'TRANSACTION')&(data.TXN<27000),:], x='TXN', shade=True)
	return fig

def trx_week(data):
	fig, ax = plt.subplots(figsize=(10, 6))
	sns.countplot(x='Day', data=data.loc[(data.Estatus== 'TRANSACTION'),:])
	ax.set_ylabel('Transctions')
	ax.set_title('Frequency of transactions by day of the week')

	return fig 

def create_clients_table(data):
	df_clientes_b0 = pd.DataFrame(pd.pivot_table(data.loc[(data.Estatus== 'TRANSACTION')], values = ['TXN','Id_product'],index='Numero_cliente', aggfunc={'TXN':np.mean, 'Id_product':'count'}))
	df_clientes_b0.reset_index(inplace = True)
	df_clientes_b1 = pd.DataFrame(pd.pivot_table(data.loc[(data.Estatus== 'APPROVED')], values = ['Importe','Tasa_Interes','CAT'],index='Numero_cliente', aggfunc={'Importe':np.max, 'Tasa_Interes':np.max, 'CAT':np.max}))
	df_clientes_b1.reset_index(inplace = True)
	df_clientes_b2 = pd.DataFrame(pd.pivot_table(data.loc[(data.Estatus== 'DELIVERED')], values = ['CP', 'Puntuacion'],index='Numero_cliente', aggfunc={'CP':np.max, 'Puntuacion':np.max}))
	df_clientes_b2.reset_index(inplace = True)
	df_clientes_b3 = data.loc[(data.Estatus== 'APPROVED'),['Numero_cliente' ,'Motivo']]
	df_merged = pd.merge(df_clientes_b1, df_clientes_b0, on='Numero_cliente', how='left')
	df_merged_2 = pd.merge(df_clientes_b3, df_clientes_b2, on='Numero_cliente', how='left')
	df_clients = pd.merge(df_merged, df_merged_2, on='Numero_cliente', how='left')
	df_clients.rename(columns = {'Numero_cliente':'CUSTOMER_ID', 'Importe':'AMOUNT_CREDIT_GRANTED', 'Id_product': 'TRANSACTIONS', 'TXN':'MEAN_AMOUNT_TRANSACTION', 'Puntuacion':'DELIVERY_SCORE','Motivo':'CARD_TYPE'}, inplace = True)
	df_clients.DELIVERY_SCORE = df_clients.DELIVERY_SCORE.astype(float)
	return df_clients 


def metrics_clients(data):
    mean_transactions = np.round(data.TRANSACTIONS.mean(),2)
    mean_transactions_amount = np.round(data.MEAN_AMOUNT_TRANSACTION.mean(),2)
    mean_delivery_score = np.round(data.DELIVERY_SCORE.mean(),2)
    mean_amount_g = np.round(data.AMOUNT_CREDIT_GRANTED.mean(),2)
    metrics = pd.DataFrame({'METRIC': ['MEAN_TRANSACTIONS', 'MEAN_TRANSACTIONS_AMOUNT', 'MEAN_DELIVERY_SCORE', 'MEAN_AMOUNT_CREDIT_GRANTED'], 
                  'VALUE': [mean_transactions, mean_transactions_amount, mean_delivery_score, mean_amount_g]})
    return metrics

st.set_page_config(page_title='Business Challenge')


nav = st.sidebar.selectbox("Menu",['Introduction', 'KPI´s and Data analysis'])

if nav == 'Introduction':

	
	
	
	st.subheader('Business Challenge Credit Cards')
	col1 , col2, col3 = st.columns([3,1,1])
	col1.markdown('Iván Serrano Zapata')
	col2.image('images/python.png',width = 50, use_column_width = False)
	col3.image('images/st.png',width = 80, use_column_width = False)
	col1.subheader('')
	



    
	with st.expander("Requirements and objectives of the challenge"):
	    	st.write("""
        	

        	1. Define and present KPI's for different stakeholders that help monitor product performance, describe the current state and facilitate future strategy

        	   

        	2. Generate an understanding data and translates into business knowledge

        	  

        	3. Generate data tables that can be used for the consumption of different business areas based on their needs

        	
        	""")

	with st.expander("Brief explanation"):
	    	st.write("""
	    		1. The dashboard is developing in [Streamlit](https://streamlit.io/),  open-source Python library used for building data science web applications. It allows you to create interactive web apps directly from Python scripts.

	    		2. For the data manipulation part i used python and conventional libraries for manipulation and visualization.

	    		3. In this [repository](https://github.com/iserranoz) you can review all the notebooks and scripts, in this application i will only show the results.

	    		""")


	with st.expander('Summary of the data'):

		st.markdown('This database contains credit card information and transactions from multiple customers')
		st.table(pd.read_csv('data/info.csv'))

    

if nav == 'KPI´s and Data analysis':

	
	df = pd.read_csv('data/data.csv')
	df = data_transform(df)
	rate_conv = '{:.2f}%'.format(100*np.round(df.loc[df.Estatus.isin(['RESPONSE']),'Numero_cliente'].count()/df.loc[df.Estatus.isin(['RESPONSE', 'NO_RESPONSE']),'Numero_cliente'].count(),4))
	rate_apro = '{:.2f}%'.format(100*np.round(df.loc[df.Estatus.isin(['APPROVED']),'Numero_cliente'].count()/df.loc[df.Estatus.isin(['RESPONSE']),'Numero_cliente'].count(),4))
	rate_f = '{:.2f}%'.format(100*np.round(df.loc[df.Estatus.isin(['APPROVED']),'Numero_cliente'].count()/df.loc[df.Estatus.isin(['RESPONSE', 'NO_RESPONSE']),'Numero_cliente'].count(),4))
	df_clients = create_clients_table(df)
	mean_amount_rx = data=df.loc[(df.Estatus== 'TRANSACTION')&(df.TXN<27000),'TXN'].mean()
	client_metrics = metrics_clients(df_clients)
	st.subheader('KPI´s and Data analysis')
	st.subheader('')
	st.subheader('')
	with st.expander("Customer acquisition"):
		st.subheader('')
		
		col1, col2 = st.columns([4,2])
		with col1:
			st.pyplot(graph_cum(df))
			st.subheader('')
			st.subheader('')
			st.pyplot(graph_pie(df))
			st.subheader('')
			st.subheader('')
			st.pyplot(graph_bar_c(df))
			st.subheader('')
			st.subheader('')


		with col2:
			st.write("""There was an accelerated growth of approved clients in the last two months of 2019, but it has slowed down considerably afterwards.""")
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.write("""Our clients prefer the physical card, but the penetration of the digital card is good.""")
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.write(f"""The conversion ratio of the campaigns is {rate_conv}, which means that almost 7 out of 10 customers 
				are interested in purchasing our product. This ratio seems to be stable in the different sales channels.
				Of that percentage, {rate_apro} are approved to have a card. Our final acquisition ratio is {rate_f}, this means that for every 10 customers we contact, around 4 get a card.""")

	with st.expander("Customer behavior"):
		st.subheader('')

		col1, col2 = st.columns([4,2])
		with col1:
			st.pyplot(graph_den(df))
			st.subheader('')
			st.subheader('')
			st.pyplot(trx_week(df))
			st.subheader('')
			st.subheader('')
			st.table(df_clients.head(10))
			st.table(client_metrics)
			st.subheader('')

		with col2:
			st.write(f"""This graph shows the distribution of transaction amounts, the average transaction amount is ${np.round(mean_amount_rx,2)}.""")
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.write("""This shows the frequency of use of the card on the days of the week, it seems that there is no type of preference in the days of card use.""")
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.write(f"""This table is very important, it groups 
				the main characteristics of our users, number of transactions made, average amount of transactions, zip code, 
				type of card, interest rate and delivery score..""")
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.subheader('')
			st.write(f"""These metrics describe the behavior of our users, and can give us an idea of the type of customer that purchases the card""")

	with st.expander("Additional KPI´s proposals"):
		st.subheader('')
		st.markdown('Performance metrics:')
		st.write("""
        	

        	1. New customers ratio: the percentage increase in new card users versus the previous month

        	   

        	2. Campaign Response Rate: The percentage of users who respond to marketing campaigns

        	  

        	3. Active Users: Percentage of users who used the credit card versus the total number of users in a month


        	4. Average delivery time: average time it takes for a card to be delivered

        	   

        	5. Usage recurrence: the average number of transactions a user makes in X time

        	 

        	
        	These metrics tend to perform better when based on some type of customer segmentation, which gives us information from different populations.""")







