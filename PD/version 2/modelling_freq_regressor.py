# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import roc_curve, auc
from sklearn.metrics import r2_score,mean_squared_error

from sklearn.datasets import make_classification

import matplotlib.pyplot as plt

import data_cleansing as dc
import data_utils as du


#%%########################################################################
#
# load the and process data
#

data_train_raw, data_test_raw = dc.load_file()

data_test_raw = dc.clean_data(data_test_raw)
data_train_raw = dc.clean_data(data_train_raw)

data_test = data_test_raw.copy()
data_train = data_train_raw.copy()

#%%########################################################################
#
# Frequency Projection
#

#%% set target
#data_train['freq'] = data_train['ClaimNb']/data_train['Exposure']
#data_test['freq'] = data_test['ClaimNb']/data_test['Exposure']
#target_name='freq'

target_name='ClaimNb'

#drop alternative targets
drop_list = [ 'Exposure', 'ClaimAmount', 'BonusMalus', 'severity', 'Claim_xs000k', 'Claim_xs100k','Claim_xs500k', 'Density']
data_train.drop(drop_list,axis='columns', inplace=True)
data_test.drop(drop_list,axis='columns', inplace=True)

#%% lable encode factors
label_encode_factors = ['Area',
                        'VehPower',
                        'VehBrand',
                        'VehGas',
                        #'Density',
                        'Region',
                        'DrivAgeBand',
                        'DensityBand',
                        'VehAgeBand']
data_train_encoded, encoders = du.preprocess_labelencode(data_train, label_encode_factors)
data_test_encoded = du.preprocess_labelencode_apply(encoders, data_test, label_encode_factors)


#%% oversample the claim ovservations to create a balanced data set
data_train_resampled = du.oversample_training_set(data_train_encoded, target_name)
#data_train_resampled = data_train_encoded.copy()
print(data_train_encoded[target_name].value_counts())
print(data_train_resampled[target_name].value_counts())


#%% split factors and target

#sets used to train (resampled sets)
x_train = data_train_resampled.drop(target_name, axis='columns')
y_train = data_train_resampled[target_name]
y_test = data_test_encoded[target_name]

#sets used to predict
x_train_to_predict = data_train_encoded.drop(target_name, axis='columns')
y_train_to_predict = data_train_encoded[target_name]
x_test = data_test_encoded.drop(target_name, axis='columns')


#%%
#
# Run frequency model
#

clf_rf = RandomForestRegressor(min_samples_leaf=5, 
                                n_estimators=70,
                                max_depth=50,
                                max_features='auto',
                                criterion='mse',    #mse or mae
                                verbose=True,
                                oob_score=True,
                                n_jobs=3)
#fit values
clf_rf = clf_rf.fit(x_train.values, y_train.values)    
#predict values
y_train_predicted_rf = clf_rf.predict(x_train_to_predict.values)    
y_test_predicted_rf = clf_rf.predict(x_test.values)   

#%%
#
# Join results back to data
#
target_name_predicted = target_name + '_predicted'
x_train_to_predict[target_name_predicted] = y_train_predicted_rf.up()
x_train_to_predict[target_name] = y_train_to_predict
x_test[target_name_predicted] = y_test_predicted_rf
x_test[target_name] = y_test

#%%
#look at claim values only

#gini results
train_results_gini = du.gini(x_train_to_predict[target_name].values, x_train_to_predict[target_name_predicted].values)
test_results_gini = du.gini(x_test[target_name].values, x_test[target_name_predicted].values)
#mean squared error
train_results_mse = mean_squared_error(x_train_to_predict[target_name].values, x_train_to_predict[target_name_predicted].values)
test_results_mse = mean_squared_error(x_test[target_name].values, x_test[target_name_predicted].values)

print('Results: ',
      'Tr_G {:,.5f}'.format(train_results_gini),
      'Te_G {:,.5f}'.format(test_results_gini),
      'Tr_mse {:,.5f}'.format(train_results_mse),
      'Te_mse {:,.5f}'.format(test_results_mse))


#%%##########################################
#
#
# Look into predictors
#
#

#%% plot distribution charts

x_train_to_predict[[target_name, target_name_predicted]].plot(kind='kde')
x_test[[target_name, target_name_predicted]].plot(kind='kde')

#%% pair plot

fig = du.plot_factors(x_train_to_predict, target_name, target_name_predicted)
fig.show()

