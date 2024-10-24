import pandas as pd
import numpy as np
import io
from datetime import datetime

from typing import Union, List
from fastapi import FastAPI, HTTPException, File, UploadFile

from supabase import create_client, Client
import os
from dotenv import load_dotenv
from .schema import AnomaliesLists_Branch, AnomaliesDetail_Branch, Branch_Feedback_Resolve, Branch_EditDetail
from .model_process import pre_processing_data, predict_data

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

app = FastAPI()

def store_to_database(df):
    try:
        data_dicts = df.to_dict(orient='records')

        response = supabase.table('Anomalies').insert(data_dicts).execute()

        if response.status_code != 200:
            raise Exception(f"Error storing data: {response}")
    except Exception as e:
        print(f"Error storing data: {e}")

@app.get("/")
def success():
    return {"status" : "deploy successfully"}


@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()
    raw_df = pd.read_csv(io.StringIO(content.decode('unicode_escape')))
    raw_df.columns = raw_df.iloc[0]
    raw_df = raw_df.drop(0).reset_index(drop=True)
    
    raw_df = raw_df.iloc[:3]
    
    raw_df.columns = [str(e).strip() for e in raw_df.columns]
    
    df = pre_processing_data(raw_df)
    
    index_that_have_error = predict_data(df)
    
    anomalies_df = raw_df.iloc[index_that_have_error]

    anomalies_df.rename(columns={
        'PRODUCT_CODE': 'product_code',
        'BRANCH': 'branch_id',
        'AREA_CODE': 'area_code',
        'ZONE_ID': 'zone_id',
        'PROVINCE_CODE': 'province_code',
        'REC_TYPE': 'rec_type',
        'DOC_TYPE': 'doc_type',
        'TRANS_TYPE': 'trans_type',
        'DOC_DATE': 'doc_date',
        'DOC_NO': 'doc_no',
        'REASON_CODE': 'reason_code',
        'CV_CODE': 'cv_code',
        'PMA_CODE': 'pma_code',
        'CATEGORY_CODE': 'category_code',
        'SUB_CATEGORY_CODE': 'subcategory_code',
        'QTY': 'quantity',
    }, inplace=True)

    anomalies_df['is_error'] = True
    anomalies_df['error_date'] = str(datetime.now().strftime('%d/%m/%Y'))
    anomalies_df['feedback'] = "Don't have feedback yet!"

    anomalies_df = anomalies_df.drop(columns=['ANOMALY', 'DESCRIPTION'])

    store_to_database(anomalies_df)
    
    return {"filename": file.filename, "status": "success"}

@app.get("/branch_ErrorList", response_model=List[AnomaliesDetail_Branch])
def read_ErrorList():
    response = supabase.table('Anomalies').select("*").execute()
    
    if response.data is None:
        raise HTTPException(status_code=500, detail=f"Error fetching data from Supabase: {response}")
    return response.data

@app.get("/branch_ErrorDetail/{product_code}", response_model=AnomaliesDetail_Branch)
def read_ErrorDetail(product_code: str):
    response = supabase.table('Anomalies').select("*").eq('product_code', product_code).single().execute()
    if response.data is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return response.data

@app.patch("/branch_Feedback/{product_code}")
def update_Feedback(product_code: str, feedback: Branch_Feedback_Resolve):
    response = supabase.table('Anomalies').update({
        'feedback': feedback.feedback,
        'is_error': feedback.is_error
    }).eq('product_code', product_code).execute()

    if response.data is None:
        raise HTTPException(status_code=500, detail="Error updating feedback")
    
    return {"feedback": "Issue resolved successfully"}

@app.patch("/audit_Feedback/{product_code}")
def update_Feedback_audit(product_code: str):
    response = supabase.table('Anomalies').update({
        'is_error': False
    }).eq('product_code', product_code).execute()

    if response.data is None:
        raise HTTPException(status_code=500, detail="Error updating feedback")
    
    return {"feedback": "Issue resolved successfully"}

@app.patch("/branch_EditDetail/{product_code}")
def update_editDetail(product_code: str, edit_detail: Branch_EditDetail):
    response = supabase.table('Anomalies').update({
        'product_code': edit_detail.product_code,
        'branch_id': edit_detail.branch_id,
        'rec_type': edit_detail.rec_type,
        'doc_type': edit_detail.doc_type,
        'trans_type': edit_detail.trans_type,
        'doc_date': edit_detail.doc_date,
        'doc_no': edit_detail.doc_no,
        'reason_code': edit_detail.reason_code,
        'cv_code': edit_detail.cv_code,
        'pma_code': edit_detail.pma_code,
        'category_code': edit_detail.category_code,
        'subcategory_code': edit_detail.subcategory_code,
        'quantity': edit_detail.quantity
    }).eq('product_code', product_code).execute()

    if response.data is None:
        raise HTTPException(status_code=500, detail="Error updating details")
    
    return {"status": "Edit Successfully"}


