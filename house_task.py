# -*- coding:utf-8 -*-
import streamlit as st
import time
import numpy as np
import pandas as pd
import time
import sqlalchemy as sqla
from datetime import timedelta, date
import altair as alt


st.write(str(time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time()))))

#engine = sqla.create_engine('mysql+pymsql://admin:T0rv4ld$mhf@192.168.1.101/housework?charset=utf8')
eng = sqla.create_engine('mysql+pymysql://admin:T0rv4ld$mhf@192.168.1.101:3307/housework?charset=utf8')

today = str(time.strftime('%Y-%m-%d',time.localtime(time.time())))

query = """SELECT * FROM task WHERE next_exe <= \"{}\";""".format(today)
#st.write(query)

df = pd.read_sql(query, eng)
#st.write(df)
if len(df):
#if st.checkbox('Show dataframe'):
#	st.write(df)

	nm = pd.read_sql("user", eng)

	name = st.selectbox(
	'我是',nm['first_name'].unique())

	option = st.selectbox(
	'今日待完成家务',
	df['descrip'].unique())

	'(已选: ', option, ', 预计耗时', (df[df['descrip'] == option]['duration'].tolist()[0]), 'min)'

	id_user = str(nm[nm['first_name'] == name]['id_user'].tolist()[0])
	id_task = str(df[df['descrip'] == option]['id_task'].tolist()[0])
	freq = str(df[df['descrip'] == option]['freq'].tolist()[0])

	def complete_task():
		query = """INSERT INTO log (id_task, id_user) VALUES ({0}, {1})""".format(id_task, id_user)
		dict = {'id_task': id_task, 'id_user': id_user}
		dt = pd.DataFrame([dict], columns=dict.keys())
		dt.to_sql('log', eng, index=False, if_exists='append')
		with eng.connect() as con:
			query = """UPDATE task set next_exe = DATE_ADD(\"{0}\" , INTERVAL {1} DAY), last_exe = \"{0}\" WHERE id_task = {2}""".format(today, freq, id_task)
			#st.write(query)

			con.execute(query)
		con.close()
		query = """SELECT descrip AS task, duration, timestamp FROM log JOIN task ON log.id_task = task.id_task WHERE log.id_user = {} AND DATE(`timestamp`) = CURDATE();""".format(id_user)
		total = 0
		ttu = pd.read_sql(query, eng)
		n = ttu.sum(axis = 0, skipna = True)
		try:
			total = n['duration']
			st.write(ttu[['task', 'duration', 'timestamp']])
		except:
			pass
		st.write(name, '今日总家务时间: ', int(total), 'min')
	if st.button('完成'):
		complete_task()
		"*-请刷新页面以继续-*"



else:
	st.write("*****")
	st.write("\n\n\n\n真棒，今天的家务都完成了！喝杯茶放松一下？")

st.write("*****")

def add_task(x):
	x += 1
	new_task = st.text_input("任务名称: ", '')
	task_dura = st.number_input('任务时长 (min)', 1, 60, 5, 1)
	task_freq = st.number_input('重复频率 (天)', 1, 365, 3, 1)
	task_init = st.date_input('开始日期')
	st.write("*****")
	st.write("将要保存任务: ", new_task)
	st.write("此任务耗时", task_dura, "分钟")
	st.write("每", task_freq, "天重复一次")
	st.write("于", task_init, "开始")
	if st.button("确认添加"):
		query = """INSERT INTO task (descrip, duration, freq, next_exe) VALUES (\'{}\', {}, {}, \'{}\')""".format(new_task, task_dura, task_freq, str(task_init))
		with eng.connect() as cursor:
			try:
				cursor.execute(query)
				st.write('任务添加成功，请刷新页面')
			except:
				st.write('无法添加任务')
		cursor.close()
	st.empty()


#st.write("查看此期间完成的家务：")
#date_from = st.date_input("自")
#date_to = st.date_input("至")

def task_done(n):
	nm = pd.read_sql("user", eng)
	d = {}
	for item in nm.index:
		dt = nm.loc[item].to_dict()
		name = dt['first_name']
		for i in range(n):
			query = """SELECT 
				SUM(duration) AS tt
			FROM
				log a
					JOIN
				user b USING (id_user)
					JOIN
				task c USING (id_task)
			WHERE
				DATE(a.timestamp) = (CURDATE() - INTERVAL {} DAY)
					AND a.id_user = {};""".format((n - 1 - i), dt['id_user'])
			try:
				temp = pd.read_sql(query, eng)['tt'][0]
			except:
				temp = 0
			if name in d:
				d[name].append(temp)
			else:
				d[name] = [temp]
#		st.write(name)
	df = pd.DataFrame.from_dict(d)
	df1 = df.T
	df = df1.rename_axis("Day", axis="columns")
	df = df.fillna(0)
	fecha = []
	for j in range(n):
		fecha.append(str(date.today() - timedelta(days=(n-j))))
	df.columns = fecha
	return df

#user_input = st.text_input("最近 _ 天的完成率", 7)
#try:
#	k = int(user_input)
#except:
#	st.write("请输入一个整数值")
#	k = 7

k = st.slider('查看近期数据（天）', 7, 30, 10)
df = task_done(int(k))
"自", date.today() - timedelta(days=(k)), "至", date.today(), ":"

data = df.loc[:]

data = data.T.reset_index()
#st.write(data)
data = pd.melt(data, id_vars=["index"]).rename(columns={"index": "Day", "value": "Total Minutes", "variable": "Name"})
#st.write(data)
chart = (
	alt.Chart(data).mark_area(opacity=0.5).encode(
		x="Day:T",
		y=alt.Y("Total Minutes:Q", stack=None),
		color="Name:N")
)
st.altair_chart(chart, use_container_width=True)

#option = st.radio('what is your favorate genre:', ['comedy', 'drama', 'documentary'])
x = st.checkbox('我要添加新的家务')
if x:
	add_task(x)

query = """SELECT 
		descrip AS task,
		duration,
		log.id_user,
		user.first_name,
		timestamp
	FROM
		log
			JOIN
		task ON log.id_task = task.id_task
			JOIN
		user ON user.id_user = log.id_user
	WHERE
		DATE(`timestamp`) = CURDATE();"""
df = pd.read_sql(query, eng)
#st.write(df)
if len(df):
	option = st.sidebar.selectbox(
	'今日已完成家务',
	df['task'].unique())
	st.sidebar.text(option)
	st.sidebar.text('此任务由 ' + (df[df['task'] == option]['first_name'].tolist()[0]) + ' 完成')
	st.sidebar.text('耗时 ' + str(df[df['task'] == option]['duration'].tolist()[0]) + ' 分钟')
	st.sidebar.text('完成时间: ' + str(df[df['task'] == option]['timestamp'].tolist()[0]))

else:
	st.sidebar.text("暂无")

