''' This script implements a regression analysis to determine composition of phases in the CT scan for the paper 
"Brief communication: High-resolution composition of permafrost cores derived from X-ray microtomography" 

Authors: Jan Nitzbon, Damir Gadylyaev, Steffen Schlüter, John Maximilian Köhne, Guido Grosse, and Julia Boike.
Script created by Damir Gadylyaev (damir.garad@gmail.com) and Jan Nitzbon (jan.nitzbon@awi.de)
March 2022'''

#%% importing libraries
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
import os

#%% loading laboratory and CT data
os.chdir('.') #the script assumes the csv files to be in the current working directory
df = pd.read_csv('./volumetric_contents_sampleRes_lab+CT.csv', skiprows=1)
mask_reg = df.depth < 81.0
nSamp = len(df[ mask_reg])
#%% prepare data as input to the ordinary least squares regression

# expanding shape of arrays
theta_o = np.expand_dims(df[mask_reg].organic_lab, axis=1)
theta_m = np.expand_dims(df[mask_reg].mineral_lab, axis=1)
theta_i = np.expand_dims(df[mask_reg].totalice_lab, axis=1)
theta_A = np.expand_dims(df[mask_reg].phaseA_CT, axis=1)
theta_B = np.expand_dims(df[mask_reg].phaseB_CT, axis=1)
theta_ei = np.expand_dims(df[mask_reg].excessice_CT, axis=1)

# dependent variable
y = np.concatenate((theta_o, theta_m, theta_i - theta_A - theta_B - theta_ei ))

# independent variable
X =  np.concatenate( ( np.concatenate( (theta_A             , np.zeros((nSamp,1))       , theta_B               , np.zeros((nSamp,1)) ) , 1 ),
                       np.concatenate( (np.zeros((nSamp,1)) , theta_A                   , np.zeros((nSamp,1))   , theta_B           )   , 1 ),
                       np.concatenate( (-theta_A            , -theta_A              ,    -theta_B               , -theta_B          )   , 1 ) ), 0 )

#%% fitting an ordinary least squares model to the data
# the four fit parameters x1..x4 are as follows:
# x1: gamma_A,o the organic fraction of phase A 
# x2: gamma_A,m the mineral fraction of phase A
# x3: gamma_B,o the organic fraction of phase B
# x4: gamma_B,m the mineral fraction of phase B
res = sm.OLS(y,X).fit()
print( res.summary() )

# composition of phase A
gamma_A_o = res.params[0] # organic in Phase A
gamma_A_m = res.params[1] # mineral in Phase A 
gamma_A_i = 1 - gamma_A_o - gamma_A_m # pore ice in Phase A

# compositoin of phase B
gamma_B_o = res.params[2] # organic in phase B
gamma_B_m = res.params[3] # mineral in phase B
gamma_B_i = 1 - gamma_B_o - gamma_B_m # ice in Phase B

#%% use the fitted parameters to predict mineral, organic and total ice based on the CT data

mineral_CT = df.phaseA_CT * gamma_A_m + df.phaseB_CT * gamma_B_m 
organic_CT = df.phaseA_CT * gamma_A_o + df.phaseB_CT * gamma_B_o 
poreice_CT = df.phaseA_CT * gamma_A_i + df.phaseB_CT * gamma_B_i
totalice_CT = poreice_CT + df.excessice_CT

# save predictions as csv file
df_pred = pd.DataFrame( np.transpose( [ poreice_CT, totalice_CT, organic_CT, mineral_CT ] ), 
                        columns=['poreice_CT', 'totalice_CT', 'organic_CT', 'mineral_CT'] )

df_all = pd.concat( [df, df_pred ], axis=1)

df_all.to_csv( './volumetric_contents_sampleRes_all.csv', index=False)

#%% evaluation metrics of the regression analysis

# total ice
print("Evaluation metrics for total ice content: ")
x = df[mask_reg].totalice_lab
y = totalice_CT[mask_reg]
res = stats.linregress(x, y)

print("slope [-] (total ice, 95%%): %0.3f +/- %0.3f" % (res.slope, res.stderr))
print("intercept [%%] (total ice, 95%%): %0.3f +/- %0.3f" % (res.intercept, res.intercept_stderr))

rsquared = res.rvalue**2
print("R² (total ice): %0.3f" % rsquared)

rmse = np.sqrt( np.mean( np.square( y-x ) ) ) 
print("RMSE (total ice): %0.3f" % rmse)

bias = np.mean( y-x )
print("bias (total ice): %0.3f" % bias)

# organic
print("Evaluation metrics for organic content: ")
x = df[mask_reg].organic_lab
y = organic_CT[mask_reg]
res = stats.linregress(x, y)

print("slope [-] (organic, 95%%): %0.3f +/- %0.3f" % (res.slope, res.stderr))
print("intercept [%%] (organic, 95%%): %0.3f +/- %0.3f" % (res.intercept, res.intercept_stderr))

rsquared = res.rvalue**2
print("R² (organic): %0.3f" % rsquared)

rmse = np.sqrt( np.mean( np.square( y-x ) ) ) 
print("RMSE (organic): %0.3f" % rmse)

bias = np.mean( y-x )
print("bias (organic): %0.3f" % bias)


# mineral
print("Evaluation metrics for mineral content: ")
x = df[mask_reg].mineral_lab
y = mineral_CT[mask_reg]
res = stats.linregress(x, y)

print("slope [-] (mineral, 95%%): %0.3f +/- %0.3f" % (res.slope, res.stderr))
print("intercept [%%] (mineral, 95%%): %0.3f +/- %0.3f" % (res.intercept, res.intercept_stderr))

rsquared = res.rvalue**2
print("R² (mineral): %0.3f" % rsquared)

rmse = np.sqrt( np.mean( np.square( y-x ) ) ) 
print("RMSE (mineral): %0.3f" % rmse)

bias = np.mean( y-x )
print("bias (mineral): %0.3f" % bias)


#%% determining high-resolution profiles of all constituents

#load high-res CT data
df_hr = pd.read_csv('./volumetric_contents_highRes_CT.csv', skiprows=1)

mineral_CT_hr = df_hr.phaseA_CT_hr * gamma_A_m + df_hr.phaseB_CT_hr * gamma_B_m 
organic_CT_hr = df_hr.phaseA_CT_hr * gamma_A_o + df_hr.phaseB_CT_hr * gamma_B_o 
poreice_CT_hr = df_hr.phaseA_CT_hr * gamma_A_i + df_hr.phaseB_CT_hr * gamma_B_i
totalice_CT_hr = poreice_CT_hr + df_hr.excessice_CT_hr

# save predictions as csv file
df_pred_hr = pd.DataFrame( np.transpose( [ poreice_CT_hr, totalice_CT_hr, organic_CT_hr, mineral_CT_hr ] ), 
                        columns=['poreice_CT_hr', 'totalice_CT_hr', 'organic_CT_hr', 'mineral_CT_hr'] )

df_all_hr = pd.concat( [df_hr, df_pred_hr ], axis=1)

df_all_hr.to_csv( './volumetric_contents_highRes_all.csv', index=False)