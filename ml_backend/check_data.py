import numpy as np
import joblib
 
data = np.load('last_20_days.npy')
scaler = joblib.load('x_scaler.pkl')
unscaled = scaler.inverse_transform(data)
 
# RELIANCE High is at column 11 (sorted: ADANIENT=0, ADANIPORTS=1, ... RELIANCE=11)
print('RELIANCE last 5 days High (col 11):')
print(unscaled[-5:, 11])
 
print('\nRELIANCE last 5 days Close - checking Open (col 11+28=39):')
print(unscaled[-5:, 39])
 
print('\nAll good - data shape:', data.shape)