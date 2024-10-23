import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import load_model
from datetime import datetime

def StripData(df):
  df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
  return df

def DeleteUnNecessaryCol(df):
  col_todrop = ['DOC_NO' ,'PRODUCT_CODE' ,'DESCRIPTION' ,'AREA_CODE','ZONE_ID','PROVINCE_CODE','BRANCH']

  df.drop(columns=col_todrop, inplace=True)
  return df

def ChangeType(df):
  changetype_col = ['AREA_CODE' , 'PROVINCE_CODE' ,'BRANCH' ,'DOC_TYPE' ,'TRANS_TYPE', 'PMA_CODE' ,'CATEGORY_CODE' ,'SUB_CATEGORY_CODE']
  for i in changetype_col :
      if i in df.columns :
          df = df.dropna(subset=[i])
          df[i] = df[i].astype(int).astype(str)
  return df


def SetSeason(date_str):
  try:
      newstr = str(date_str).lstrip()
      date = datetime.strptime(newstr, '%d/%m/%Y')
      m = date.month
      if m in [12, 1, 2]:
          return 'winter'
      elif m in [3, 4, 5]:
          return 'spring'
      elif m in [6, 7, 8]:
          return 'summer'
      else:
          return 'fall'
  except ValueError:
      return 'unknown'
  
def label_cv_code(x) :
  if isinstance(x, str):
    if x == '' :
      return "Unknown"
    elif x[0].isalpha():
      return "Enterprise"
    elif x.isnumeric():
      return "Out-source"
    else:
      return "Unknown"
  return "Unknown"

def TransformToSTR(df):
  le = LabelEncoder()
  col = ['AREA_CODE', 'ZONE_ID', 'PROVINCE_CODE', 'BRANCH',
         'DOC_TYPE', 'TRANS_TYPE', 'CV_CODE','PMA_CODE',
         'CATEGORY_CODE','SUB_CATEGORY_CODE' ,'REC_N_SEASON' ,'SEASON' ,'ANOMALY']
  for i in col:
      if i in df.columns:
          df[i] = le.fit_transform(df[i].astype(str))
  return df

def pre_processing_data(df) :
  #df_t = df_t.iloc[:3] this line is for testing
  
  df.columns = [str(e).strip() for e in df.columns]
  
  print(df.columns)
  
  #Strip Data
  df = StripData(df)
  
  #Delete unnecessary Columns
  df = DeleteUnNecessaryCol(df)
  
  #Set Types Data
  df = ChangeType(df)

  #Feature Engineering - REC+REASON_CODE
  df['REC_TYPE'] = df['REC_TYPE'].astype(str)
  df['REASON_CODE'] = df['REASON_CODE'].astype(str)
  df['REC_N_SEASON'] = df['REC_TYPE'] + '-' + df['REASON_CODE']
  df.drop(columns=['REC_TYPE' , 'REASON_CODE'] ,inplace=True)

  #Feature Engineering - CV_CODE -> who trans it?
  df['CV_CODE'] = df['CV_CODE'].apply(lambda x: x.strip() if isinstance(x, str) else x)
  df['CV_CODE'] = df['CV_CODE'].apply(label_cv_code)

  #Feature Engineering - CV_CODE -> Season Detectec
  df['SEASON'] = df['DOC_DATE'].apply(SetSeason)
  df.drop(columns=['DOC_DATE'], inplace=True)
  
  #Encoding (LabelEncoding)
  df = TransformToSTR(df.copy(deep=True))
  
  return df

def predict_data(df) :
  #Loading Model
  path_Model_AutoEncoder = './model_and_scaler/best_model.keras' 
  path_Model_RandomForest = './model_and_scaler/random_forest_classifier.pkl'
  
  AutoEncoder_Model = load_model(path_Model_AutoEncoder)
  RandomForest_Model = joblib.load(path_Model_RandomForest)
  
  #Loading Scaler
  path_Scaler = './model_and_scaler/scaler.pkl'
  scaler = joblib.load(path_Scaler)
  
  #Scaling Data
  temp_df = df.copy(deep=True).drop(columns= ['ANOMALY'])
  temp_scaled_df = scaler.transform(temp_df)
  
  #Predict
  AutoEncoder_predictions = AutoEncoder_Model.predict(temp_scaled_df)
  
  #Prepare Data Before Classified
  df_reconstruction_error = np.mean(np.power(temp_scaled_df - AutoEncoder_predictions, 2), axis=1)
  df_reconstruction_error = df_reconstruction_error.reshape(-1, 1)
  
  temp_df_with_error = np.hstack((temp_scaled_df, df_reconstruction_error.reshape(-1, 1)))
  
  #Classified
  randomForest_prediction = RandomForest_Model.predict(temp_df_with_error)
  
  #Usage
  index_that_have_error = []
  i = 0
  for value in randomForest_prediction :
    if (value) :
      index_that_have_error.append(i)
    i+=1
    
  return index_that_have_error