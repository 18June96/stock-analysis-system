import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def st_data(nm, info, selected_year, top_n):
    #nm--申万行业名称
    #info--申万行业分类表
    
    #1.读取相关数据
    data=pd.read_csv('index_trdata.csv')
    trdata=pd.read_csv('stk_trdata.csv')
    findata=pd.read_csv('fin_data.csv')
    co_data=pd.read_excel('上市公司基本信息.xlsx')
    
    #2.筛选指定行业的行业指数交易数据，并要求行业指数交易数据大于600条记录,同时返回该交易数据
    data_i=data.iloc[data['name'].values==nm,:]
    data_i=data_i.sort_values(['trade_date'])
    data_i.columns=['指数代码','行业名称','交易日期','开盘指数','收盘指数','成交量','市盈率','市净率']
    
    f1 = None
    f2 = None
    eval_result = None
    
    if len(data_i)>600:
        #3.绘制行业收盘指数走势图，返回图像句柄变量f1
        plt.rcParams['font.sans-serif'] = 'SimHei'     # 设置字体为SimHei
        plt.figure(1)
        f1,ax=plt.subplots()
        plt.title('申万'+nm+'行业指数走势图')
        x1=data_i['交易日期'].values
        y1=data_i['收盘指数'].values
        plt.plot(range(len(x1)),y1)
        plt.xticks([0,100,200,300,400,500,600],x1[[0,100,200,300,400,500,600]],rotation=45)
       
        #4.关联获得行业相关的上市公司基本信息co_data和相关股票交易数据trdata_hy，并返回
        chy_code=info.iloc[(info['新版一级行业'].values==nm)&(info['交易所'].values=='A股'),[2,3]]
        chy_code.columns=['ts_code','nm']
        co_data=pd.merge(co_data,chy_code,how='inner',on='ts_code')
        
        trdata_hy=pd.merge(trdata,chy_code,how='inner',on='ts_code')
        trdata_hy=trdata_hy.sort_values(['ts_code','trade_date'])
        trdata_hy.columns=['股票代码','交易日期','收盘价','成交量','成交金额','股票简称']
        
        #5.绘制行业相关股票交易数据走势图（子图，选6个股票，要求交易记录大于600条），并返回图像句柄变量f2
        code=list(set(trdata_hy['股票代码'].values))
        plt.figure(2)
        plt.figure(figsize=(12,8))
        f2,ax=plt.subplots()
        p=0
        for i in range(len(code)):
                trdata_k=trdata_hy.iloc[trdata_hy['股票代码'].values==code[i],[1,2,-1]]
                if len(trdata_k)>600:
                    p=p+1
                    trdata_k.index=range(len(trdata_k))
                    x2=trdata_k['交易日期'].values
                    y2=trdata_k['收盘价'].values
                    plt.subplot(3,2,p)
                    plt.title(trdata_k.iloc[0,2])
                    plt.plot(range(len(x2)),y2)
                    plt.xticks([0,100,200,300,400,500,600],x2[[0,100,200,300,400,500,600]],rotation=45)
                if p==6:
                    break
        plt.tight_layout()
        
        #6.返回行业相关股票的财务指标数据
        code_p=pd.DataFrame(code)
        code_p.columns=['股票代码']
        findata_m=pd.merge(findata,code_p,how='inner',on='股票代码')
        
        #7.计算综合评价结果（关联股票简称）
        # 从co_data中获取股票简称
        name_map = co_data.set_index('ts_code')['nm'].to_dict()
        findata_m['股票简称'] = findata_m['股票代码'].map(name_map)
        
        eval_result = F_score(findata_m, selected_year, top_n)
        
        return (f1,f2,data_i,findata_m,trdata_hy,co_data.iloc[:,:-1], eval_result)
    
    return (f1,f2,data_i,None,trdata_hy,co_data.iloc[:,:-1], eval_result)


def F_score(findata,selected_year,top_n):
    #计算总体规模与投资效率的综合得分+排名
    #筛选指定年份的财务数据
    findata_year = findata[findata['年度'] == selected_year]    
    findata_year = findata_year.dropna(subset=['总资产', '净资产收益率'])     #缺失值处理
    
    if len(findata_year) == 0:
        return pd.DataFrame(columns=['股票代码', '股票简称', '总资产', '净资产收益率', '综合得分'])
    
    # 数据标准化-Min-Max归一化
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    
    # 规模得分--总资产
    findata_year['规模得分'] = scaler.fit_transform(findata_year[['总资产']])
    
    # 效率得分--净资产收益率
    findata_year['效率得分'] = scaler.fit_transform(findata_year[['净资产收益率']])
    
    #主成分分析（PCA）
    from sklearn.decomposition import PCA
    #提取需要分析的指标列
    pca_data = findata_year[['规模得分', '效率得分']]
    #初始化PCA，提取1个主成分
    pca = PCA(n_components=1)
    
    #计算主成分得分
    findata_year['主成分得分'] = pca.fit_transform(pca_data)
    #主成分得分直接作为综合得分
    findata_year['综合得分'] = findata_year['主成分得分']
    
    result = findata_year.sort_values('综合得分', ascending=False).head(top_n)    #降序排名

    #返回所需字段
    return result[['股票代码', '股票简称', '总资产', '净资产收益率', '综合得分']]

def st_fig():
    info=pd.read_excel('最新个股申万行业分类(完整版-截至7月末).xlsx')
    nm_L=list(set(info['新版一级行业'].values))

    nm=nm_L[0]
    
    # 设置页面的标题、图标和布局
    st.set_page_config(
            page_title="基于总体规模与投资效率的综合评价",  # 页面标题
            layout='wide',
        )
        
    with st.sidebar:
        st.subheader('请选择指数&行业')
        nm = st.selectbox(" ", nm_L)
        
    
    if nm:
       r=st_data(nm,info, selected_year=None, top_n=None)
    
       left, right = st.columns(2)

       with left:
           st.subheader('指数走势图')
           st.pyplot(r[0])
       with right:
           st.subheader('前6只股票价格走势图')
           st.pyplot(r[1])
       
       st.subheader('指数交易数据')
       st.dataframe(r[2],use_container_width=True)     # 添加',use_container_width=True'——实现自适应
       st.subheader('相关上市公司基本信息')
       st.dataframe(r[5])       
       st.subheader('相关上市公司股票财务数据')
       st.dataframe(r[3])
       st.subheader('相关上市公司股票交易数据(前2000条)')
       st.dataframe(r[4].iloc[:2000,],use_container_width=True)
       
       st.subheader('基于总体规模与投资效率的综合评价')
       st.markdown('通过下拉选择框，选择不同的年度、前5、10、15、20的综合排名结果')
       
       st.subheader('选择年度-查看综合排名')
       select_col1, select_col2 = st.columns(2)
       with select_col1:
           selected_year = st.selectbox("选择年份", options=[2022, 2023, 2024], index=0)
           with select_col2:
               top_n = st.selectbox("选择排名数量", options=[5, 10, 15, 20], index=0)
       #根据选择的参数计算综合评价结果
       eval_result = F_score(r[3], selected_year, top_n)

       eval_result = eval_result.reset_index(drop=True)  #重置索引——.reset_index(drop=True)
       st.dataframe(eval_result,use_container_width=True)

st_fig()







