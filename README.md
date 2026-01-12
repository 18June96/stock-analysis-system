# 基于Streamlit的行业股票分析与综合评价系统技术文档
## 一、项目概述
　　本系统目的是为用户提供一个可视化的工具，用于分析特定行业的市场表现和公司财务健康状况。用户可以选择一个行业，查看其指数历史走势、代表性个股的走势，并基于财务指标对行业内公司进行综合排名。  
　　**数据处理流程**：读取数据 → 筛选行业 → 清洗整理 → 分析计算 → 可视化展示
## 二、技术栈
　　Python、Streamlit、Pandas、Matplotlib绘制图、Scikit-learn (用于数据标准化和主成分分析)
## 三、数据源
　　指数交易数据.csv ————行业指数的历史交易记录；  
　　股票交易数据.csv ————所有上市公司的股票交易记录；  
　　财务数据.csv ————上市公司的财务指标数据；  
　　上市公司基本信息.xlsx ————公司的基本注册和分类信息；  
　　最新个股申万行业分类(完整版-截至7月末).xlsx ————用于映射股票代码与申万一级行业。  
　　**数据来源**：https://tushare.pro/
## 四、核心功能模块
该程序主要由三个函数构成：
#### 4.1 数据处理与计算模块: st_data(nm, info, selected_year, top_n)
此函数是数据处理的核心，负责根据用户选择的行业名称获取并处理所有相关数据。  
　　1）输入参数:  
　　　　nm (str): 申万一级行业名称（例如：“电子”、“医药生物”）。  
　　　　info (DataFrame): 申万行业分类表。  
　　　　selected_year (int): 选择的年份（用于财务分析）。  
　　　　top_n (int): 显示排名前 N 的公司。  
　　2）处理流程:  
　　　　数据加载: 读取上述 5 个数据文件。  
　　　　行业筛选: 从“指数交易数据”中筛选出指定行业的数据，并按日期排序。  
　　　　数据过滤: 只有当该行业的历史指数记录大于 600 条时，才会继续进行绘图和深度分析。  
　　　　关联查询: 利用“申万行业分类表”作为桥梁，关联出该行业内所有的上市公司代码，并进一步提取这些公司在“股票交易数据”和“财务数据”中的记录。  
　　　　返回结果: 返回包含图表对象、数据表格及综合评价结果的元组。  
```python
  def st_data(nm, info, selected_year, top_n):
    # nm--申万行业名称
    # info--申万行业分类表
    # selected_year: 选择的年份
    # top_n: 显示前N名
    
    # 1.读取相关数据
    data=pd.read_csv('指数交易数据.csv')     
    trdata=pd.read_csv('股票交易数据.csv')      
    findata=pd.read_csv('财务数据.csv')       
    co_data=pd.read_excel('上市公司基本信息.xlsx')
    
    # 2.筛选指定行业的行业指数交易数据，并要求行业指数交易数据大于600条记录,同时返回该交易数据
    data_i=data.iloc[data['name'].values==nm,:]
    data_i=data_i.sort_values(['trade_date'])
    # 重命名列名（中文更易读）
    data_i.columns=['指数代码','行业名称','交易日期','开盘指数','收盘指数','成交量','市盈率','市净率']
    
    # 初始化三个变量为None，防止未定义错误
    f1 = None
    f2 = None
    eval_result = None
```
#### 4.2 综合评价引擎: F_score(findata, selected_year, top_n)  
该函数基于财务指标的综合实现打分模型，用于评估公司的“总体规模”与“投资效率”。  
　　· 算法逻辑:  
　　　　1）数据筛选: 根据用户选择的年份筛选财务数据，并剔除缺失值。  
　　　　2）指标选取:  
　　　　　　总体规模: 使用 总资产 作为衡量指标。  
　　　　　　投资效率: 使用 净资产收益率 作为衡量指标。  
　　　　3）数据标准化: 使用 MinMaxScaler 将不同量纲的指标归一化到 [0, 1] 区间。  
　　　　4）主成分分析: 使用 PCA 将“规模得分”和“效率得分”合并为一个“综合得分”。  
　　　　5）输出: 按综合得分降序排列，返回前 N 名的公司列表。  
```python
# 综合评价函数
def F_score(findata,selected_year,top_n):
    #计算总体规模与投资效率的综合得分+排名
    # 1.筛选指定年份的财务数据
    findata_year = findata[findata['年度'] == selected_year]    
    findata_year = findata_year.dropna(subset=['总资产', '净资产收益率'])     #缺失值处理
    
    if len(findata_year) == 0:
        return pd.DataFrame(columns=['股票代码', '股票简称', '总资产', '净资产收益率', '综合得分'])
    
    # 2.数据标准化处理
    # Min-Max归一化
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    
    # 规模得分--总资产
    findata_year['规模得分'] = scaler.fit_transform(findata_year[['总资产']])
    
    # 效率得分--净资产收益率
    findata_year['效率得分'] = scaler.fit_transform(findata_year[['净资产收益率']])
    
    # 3.主成分分析（PCA）
    from sklearn.decomposition import PCA
    #提取需要分析的指标列
    pca_data = findata_year[['规模得分', '效率得分']]
    #初始化PCA，提取1个主成分
    pca = PCA(n_components=1)
    
    #计算主成分得分
    findata_year['主成分得分'] = pca.fit_transform(pca_data)
    #主成分得分直接作为综合得分
    findata_year['综合得分'] = findata_year['主成分得分']
    
    # 4.排序返回结果
    result = findata_year.sort_values('综合得分', ascending=False).head(top_n)    #降序排名
    return result[['股票代码', '股票简称', '总资产', '净资产收益率', '综合得分']]
```
#### 4.3 前端界面模块: st_fig()  
该函数负责构建 Streamlit 用户界面。  
　　界面布局:  
　　　　· 侧边栏: 包含一个下拉选择框，用于选择申万一级行业。  
　　　　· 主区域:  
　　　　　　1）图表区: 左右两栏分别展示“行业指数走势图”和“前6只个股价格走势图”。  
　　　　　　2）数据区: 依次展示原始数据表格（指数数据、公司信息、财务数据、交易数据）。  
　　　　　　3）评价区: 包含年份和排名数量的选择器，以及最终的综合排名结果表格。  
```python
def st_fig():
    # 1.获取所有行业名称列表，默认选择第一个
    info=pd.read_excel('最新个股申万行业分类(完整版-截至7月末).xlsx')
    nm_L=list(set(info['新版一级行业'].values))
    nm=nm_L[0]
    
    # 2. 页面配置：设置页面的标题、图标和布局
    st.set_page_config(
            page_title="基于总体规模与投资效率的综合评价",  # 页面标题
            layout='wide',
        )
    # 3.侧边栏
    with st.sidebar:
        st.subheader('请选择指数&行业')
        nm = st.selectbox(" ", nm_L)
    
    # 4.数据显示布局
    if nm:
       r=st_data(nm,info, selected_year=None, top_n=None)
    
       left, right = st.columns(2)
 
       with left:
           st.subheader('指数走势图')
           st.pyplot(r[0])
       with right:
           st.subheader('前6只股票价格走势图')
           st.pyplot(r[1])
       
       # 5.数据显示
       st.subheader('指数交易数据')
       st.dataframe(r[2],use_container_width=True)     # 添加',use_container_width=True'——实现自适应
       st.subheader('相关上市公司基本信息')
       st.dataframe(r[5])       
       st.subheader('相关上市公司股票财务数据')
       st.dataframe(r[3])
       st.subheader('相关上市公司股票交易数据(前2000条)')
       st.dataframe(r[4].iloc[:2000,],use_container_width=True)
       
       # 6.综合评价选择器
       st.subheader('基于总体规模与投资效率的综合评价')
       st.markdown('通过下拉选择框，选择不同的年度、前5、10、15、20的综合排名结果')
       
       st.subheader('选择年度-查看综合排名')
       select_col1, select_col2 = st.columns(2)
       with select_col1:
           selected_year = st.selectbox("选择年份", options=[2022, 2023, 2024], index=0)
           with select_col2:
               top_n = st.selectbox("选择排名数量", options=[5, 10, 15, 20], index=0)
       # 7.根据选择的参数计算综合评价结果
       eval_result = F_score(r[3], selected_year, top_n)
 
       eval_result = eval_result.reset_index(drop=True)  #重置索引——.reset_index(drop=True)
       st.dataframe(eval_result,use_container_width=True)
```
## 五、Streamlit页面展示
<img width="1860" height="845" alt="image" src="https://github.com/user-attachments/assets/8ff0c426-0eb3-4ca8-a6df-b350ff331e7a" />  
<img width="1860" height="794" alt="image" src="https://github.com/user-attachments/assets/9e3ae904-612c-4d2b-924c-b9cbdf97e44f" />

## 六、注意事项与优化建议
　　文件路径: 代码中使用了相对路径。如果文件不在同一目录，需要修改 pd.read_csv 和 pd.read_excel 中的路径。  
　　数据量检查: 代码中强制要求行业指数数据大于 600 条才进行绘图，这可能会导致部分数据量较小的新兴行业无法显示图表。  
　　图表优化: 当前的 Matplotlib 图表在 Streamlit 中显示时，如果数据点过多（如 600+），X 轴的日期标签可能会重叠。建议使用交互式图表库（如 Plotly）替代 Matplotlib 以获得更好的缩放体验。  
　　缓存机制: 由于数据读取和 PCA 计算可能耗时，建议在 Streamlit 函数上添加 @st.cache_data 装饰器，以避免用户交互时重复计算。  
## 七、总结
　　本文详细解析的金融数据分析系统展示了如何将复杂金融分析流程转化为直观易用的Web应用，通过本项目，我们可以看到数据科学、金融分析和Web开发的完美结合，为传统金融分析工作提供现代化的解决方案。
