# -*- coding: utf-8 -*-
"""97232_Analysis.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1k3p1-WpvIdWvEhNzXXly_VcLGStZoRwP
"""

!pip install pmdarima --q

# Commented out IPython magic to ensure Python compatibility.
# Magic function that will make your plot outputs appear and be stored within the notebook
# %matplotlib inline

# Function used to to render higher resolution images
# %config InlineBackend.figure_format = 'retina'

# Ignore all warnings
import warnings
warnings.filterwarnings("ignore")

# Reproducibility
import random

# Data manipulation
import os
import pandas as pd
import numpy as np
from datetime import datetime, date

pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

# Data visualization
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as msno

# Standardizing the style for the visualizations
sns.set_theme()
sns.set_palette("pastel")
plt.style.use('seaborn-whitegrid')

# Machine learning models and utilities
from sklearn.metrics import mean_absolute_error, mean_squared_error
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_predict
import pmdarima as pm
from prophet import Prophet
import math
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

# Seed value for reproducibility
SEED = 29

# Seeding all the notebook for reproducibility purposes
def seed_it(SEED):

    np.random.seed(SEED)
    random.seed(SEED)

    print('Notebook has been seeded successfully')

seed_it(SEED)

# Principal path
path= "/content/Analysis"

# Training path
train= "97232.xlsx"

df=pd.read_excel(os.path.join(path,train))

df.head(3).append(df.tail(3))

print('The total number of rows in the dataset is: ',len(df))

type(df['Date'][0])

df['Date'] =pd.to_datetime(df['Date'], format = '%d-%m-%Y')
type(df['Date'][0])

# Table showing the number of missing values and percentage
# of missing values in the current dataset
dict = {}
for i in list(df.columns):
    dict[i] = (df[i].isnull().sum(),round(df[i].isnull().sum()/len(df)*100,2))

pd.DataFrame(dict,index=["# of missing values","% of missing values"]).transpose().sort_values(by=["# of missing values"], ascending=False)

# Plotting each of the time series
fig, ax =plt.subplots(nrows=7,ncols=1,figsize=(8,8))
sns.despine()

for i, column in enumerate(df.drop('Date', axis=1).columns):
    sns.lineplot(x=df['Date'], y=df[column], ax=ax[i])
    ax[i].set_title('Variabel: {}'.format(column), fontsize=14)
    ax[i].set_ylabel(ylabel=column, fontsize=10)

plt.tight_layout()

df.isna().sum()

np.isinf(df).sum()

df.isnull().sum()

df.dropna(axis=0)

df.isnull().sum()

# Function for outlier removal
def remove_outlier(df_in, col_name):
    q1 = df_in[col_name].quantile(0.25)
    q3 = df_in[col_name].quantile(0.75)
    iqr = q3-q1 #Interquartile range
    fence_low  = q1-1.5*iqr
    fence_high = q3+1.5*iqr
    df_out = df_in.loc[(df_in[col_name] > fence_low) & (df_in[col_name] < fence_high)]
    return df_out

mean_pre= remove_outlier(df,'Tx')

# Plotting meaenpressure w/o outliers for a better visualization
fig, ax =plt.subplots(figsize=(8,3))
sns.despine()
ax.set_title('Tx - w/o outliers', size=14)
sns.lineplot(data=mean_pre,x='Date',y='Tx')

plt.tight_layout()

# Replacing outliers with NaN values
def replace_outliers(df_in, col_name):
    q1 = df_in[col_name].quantile(0.25)
    q3 = df_in[col_name].quantile(0.75)
    iqr = q3-q1 #Interquartile range

    df_in.loc[(df[col_name]<q1-1.5*iqr) | (df[col_name]>q3 + 1.5*iqr),col_name] = np.nan

    return df_in

# Quantifying how many NaN value we have after replace_outliers was applied
print('Total NaN values for Tx',df['Tx'].isnull().sum())

df = df.ffill()

# meanpressure NaN values after interpolation
print('Total NaN values for Tx',df.isnull().sum())

# Downsampling dataset Days -> Week
downsample = df[['Date',
                 'Tx',
                 'Tavg',
                 'RH_avg',
                 'RR_2' ,
                 'ss' ,
                 'ff_avg' ,
                 'TCI'
                ]].resample('7D', on='Date').mean().reset_index(drop=False)

df = downsample.copy()

print('The total number of rows dataset after downsampling: ',len(df))

# Function to visualize Augmented Dickey–Fuller test
def visualize_adfuller_results(series, title, ax):
    result = adfuller(series)
    significance_level = 0.05
    adf_stat = result[0]
    p_val = result[1]
    crit_val_1 = result[4]['1%']
    crit_val_5 = result[4]['5%']
    crit_val_10 = result[4]['10%']

    if (p_val < significance_level) & ((adf_stat < crit_val_1)):
        linecolor = 'forestgreen'
    elif (p_val < significance_level) & (adf_stat < crit_val_5):
        linecolor = 'orange'
    elif (p_val < significance_level) & (adf_stat < crit_val_10):
        linecolor = 'red'
    else:
        linecolor = 'purple'
    sns.lineplot(x=df['Date'], y=series, ax=ax, color=linecolor)
    ax.set_title(f'ADF Statistic {adf_stat:0.3f}, p-value: {p_val:0.3f}\nCritical Values 1%: {crit_val_1:0.3f}, 5%: {crit_val_5:0.3f}, 10%: {crit_val_10:0.3f}', fontsize=14)
    ax.set_ylabel(ylabel=title, fontsize=14)

# Plotting Augmented Dickey–Fuller test results for each column
fig, ax =plt.subplots(nrows=7,ncols=1,figsize=(8,8))

visualize_adfuller_results(df['Tx'].values, 'Tx', ax[0])
visualize_adfuller_results(df['Tavg'].values, 'Tavg', ax[1])
visualize_adfuller_results(df['RH_avg'].values, 'RH_avg', ax[2])
visualize_adfuller_results(df['RR_2'].values, 'RR', ax[3])
visualize_adfuller_results(df['ss'].values, 'ss', ax[4])
visualize_adfuller_results(df['ff_avg'].values, 'ff_avg', ax[5])
visualize_adfuller_results(df['TCI'].values, 'TCI', ax[6])

plt.tight_layout()

# Decomposing time series
columns=['Tx','Tavg','RH_avg','RR_2', 'ss', 'ff_avg']

fig, ax =plt.subplots(nrows=2,ncols=7,figsize=(20,5))

for i, column in enumerate(columns):

    res = seasonal_decompose(df[column], period=52, model='additive', extrapolate_trend='freq')

    ax[0,i].set_title('Dekomposisi  {}'.format(column), fontsize=16)
    res.observed.plot(ax=ax[0,i], legend=False)
    ax[0,i].set_ylabel('', fontsize=14)

    res.trend.plot(ax=ax[1,i], legend=False)
    ax[1,i].set_ylabel('Trend', fontsize=14)


plt.tight_layout()

# Plotting only seasonality for each column
for column in columns:
    decomp = seasonal_decompose(df[column], period=52, model='additive', extrapolate_trend='freq')
    df[f"{column}_trend"] = decomp.trend
    df[f"{column}_seasonal"] = decomp.seasonal

fig, ax =plt.subplots(nrows=7,ncols=1,figsize=(15,12))

for i, column in enumerate(columns):
    sns.lineplot(x=df['Date'], y=df[column + '_seasonal'], ax=ax[i])
    ax[i].set_ylabel(ylabel=column, fontsize=14)

plt.tight_layout()

# Plotting correlation heatmap of the dataset
corr=df[columns].corr()
mask= np.triu(np.ones_like(corr,dtype=np.bool))
fig,ax= plt.subplots(figsize=(5,5))
sns.heatmap(corr, annot=True, fmt=".2f",cbar_kws={"shrink": .8}, vmin=0, vmax=1, square=bool)
None

# Defining training dataset size (85%)
train_size = int(0.85 * len(df))

# Defining univariate Dataframe - Target = humidity
univariate_df=df[['Date', 'TCI']].copy()
univariate_df.columns = ['ds', 'y']

# Train - Validation split
train = univariate_df.iloc[:train_size, :]

x_train, y_train = pd.DataFrame(univariate_df.iloc[:train_size, 0]), pd.DataFrame(univariate_df.iloc[:train_size, 1])
x_valid, y_valid = pd.DataFrame(univariate_df.iloc[train_size:, 0]), pd.DataFrame(univariate_df.iloc[train_size:, 1])

# Tunning ARIMA model with AutoArima
model = pm.auto_arima(y_train, start_p=0, start_q=0,
                      test='adf',
                      max_p=3, max_q=3,
                      m=1,
                      d=None,
                      seasonal=False,
                      start_P=0,
                      D=0,
                      trace=True,
                      error_action='ignore',
                      suppress_warnings=True,
                      stepwise=True)

# Defining and fiting ARIMA model
model = ARIMA(y_train, order=(1,0,1),trend='c')
model_fit = model.fit()
print(model_fit.summary())

# Prediction with ARIMA
y_pred = model_fit.forecast(87)

score_mae = mean_absolute_error(y_valid, y_pred)
score_rmse = math.sqrt(mean_squared_error(y_valid, y_pred))

print('RMSE: {}'.format(score_rmse))

# Plotting forecast - ARIMA univariate analysis
fig, ax = plt.subplots(figsize=(10, 4))

sns.lineplot(x=x_train.index, y=y_train['y'], ax=ax)
sns.lineplot(x=x_valid.index, y=y_valid['y'], ax=ax, label='Ground truth')
plot_predict(model_fit,487, 574, ax=ax)

ax.set_title(f'Prediction \n MAE: {score_mae:.2f}, RMSE: {score_rmse:.2f}', fontsize=14)
ax.set_xlabel(xlabel='Date', fontsize=14)
ax.set_ylabel(ylabel='TCI', fontsize=14)

plt.tight_layout()

# Defining multivariate Dataframe - Target = humidity
features= ['Tx',
          'Tavg',
          'RH_avg',
          'RR_2',
          'ss',
          'ff_avg']

target=['TCI']

multivariate_df= df[['Date'] + target + features].copy()
multivariate_df.columns = ['ds', 'y'] + features

multivariate_df.head(5).append(multivariate_df.tail(5))

# Train - Validation split
train = multivariate_df.iloc[:train_size, :]
x_train, y_train = pd.DataFrame(multivariate_df.iloc[:train_size, [0,2,3,4]]), pd.DataFrame(multivariate_df.iloc[:train_size, 1])
x_valid, y_valid = pd.DataFrame(multivariate_df.iloc[train_size:, [0,2,3,4]]), pd.DataFrame(multivariate_df.iloc[train_size:, 1])

# Train the model
model = Prophet()
model.add_regressor('Tx'),
model.add_regressor('Tavg'),
model.add_regressor('RH_avg'),

# Fit the model with train set
model.fit(train)

# Predict on valid set
y_pred = model.predict(x_valid)

# Calcuate metrics
score_mae = mean_absolute_error(y_valid, y_pred['yhat'])
score_rmse = math.sqrt(mean_squared_error(y_valid, y_pred['yhat']))

print('RMSE: {}'.format(score_rmse))

# Plotting forecast - Prophet multivariate analysis
fig, ax = plt.subplots(figsize=(10, 4))

model.plot(y_pred, ax=ax)
sns.lineplot(x=x_train['ds'], y=y_train['y'], ax=ax, label='Train Set')
sns.lineplot(x=x_valid['ds'], y=y_valid['y'], ax=ax, color='orange', label='Ground truth')

ax.set_title(f'Prediction \n MAE: {score_mae:.2f}, RMSE: {score_rmse:.2f}', fontsize=14)
ax.set_xlabel(xlabel='Date', fontsize=14)
ax.set_ylabel(ylabel='TCI', fontsize=14)

plt.tight_layout()