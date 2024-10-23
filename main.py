import pandas as pd
import numpy as np
import io
from datetime import datetime


from typing import Union ,List
from sqlalchemy.orm import Session

from fastapi import FastAPI , Request ,Depends ,HTTPException ,File , UploadFile


from .database import engine ,Base ,get_db 
from .schema import AnomaliesLists_Branch ,AnomaliesDetail_Branch ,Branch_Feedback_Resolve ,Branch_EditDetail
from .models import CSVData
from .model_process import pre_processing_data ,predict_data

# Recreate the table
Base.metadata.create_all(bind=engine)

app = FastAPI()

def store_to_database(df, db):
    try:
        data_dicts = df.to_dict(orient='records')
        data_objects = [CSVData(**data) for data in data_dicts]
        db.bulk_save_objects(data_objects)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error storing data: {e}")


@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    raw_df = pd.read_csv(io.StringIO(content.decode('unicode_escape')))
    raw_df.columns = raw_df.iloc[0]
    raw_df = raw_df.drop(0).reset_index(drop=True)
    
    # raw_df = raw_df.iloc[:3] # this line is for testing
    print(raw_df)
    
    raw_df.columns = [str(e).strip() for e in raw_df.columns]
    
    df = pre_processing_data(raw_df)
    
    index_that_have_error = predict_data(df)
    
    anomalies_df = raw_df.iloc[index_that_have_error]
    
    #After Detecting
    anomalies_df.rename(columns={
        'PRODUCT_CODE': 'product_code', #1
        'BRANCH': 'branch_id', #2
        'AREA_CODE': 'area_code', #3
        'ZONE_ID': 'zone_id', #4
        'PROVINCE_CODE': 'province_code', #5
        'REC_TYPE': 'rec_type', #6
        'DOC_TYPE': 'doc_type', #7
        'TRANS_TYPE': 'trans_type', #8
        'DOC_DATE': 'doc_date', #9
        'DOC_NO': 'doc_no', #10
        'REASON_CODE': 'reason_code', #11
        'CV_CODE': 'cv_code', #12 
        'PMA_CODE': 'pma_code', #13 
        'CATEGORY_CODE': 'category_code', #14
        'SUB_CATEGORY_CODE': 'subcategory_code', #15
        'QTY': 'quantity', #16
    }, inplace=True)
    
    
    anomalies_df['is_error'] = True #17
    anomalies_df['error_date'] = str(datetime.now().strftime('%d/%m/%Y')) #18
    anomalies_df['feedback'] = str('Don\'t have feedback yet!')
    
    anomalies_df = anomalies_df.drop(columns= ['ANOMALY' ,'DESCRIPTION'])
    print('anomalies data :')
    print(anomalies_df)
    store_to_database(anomalies_df, db)
    
    
    return {"filename": file.filename, "status": "success"}

@app.get("/branch_ErrorList" , response_model=List[AnomaliesDetail_Branch])
def read_ErrorList(db: Session = Depends(get_db) ):
    db_item = db.query(CSVData).all()
    
    return db_item

@app.get("/branch_ErrorDetail/{product_code}" , response_model= AnomaliesDetail_Branch)
def read_ErrorList(product_code: str, db: Session = Depends(get_db)):
    db_item = db.query(CSVData).filter(CSVData.product_code == product_code).first()
    if db_item is None :
        raise HTTPException(status_code=404 , detail="Item not found")
    
    return db_item

@app.patch("/branch_Feedback/{product_code}")
def update_Feedback(product_code: str , feedback:Branch_Feedback_Resolve,db: Session = Depends(get_db)):
    db_item = db.query(CSVData).filter(CSVData.product_code == product_code).first()
    if db_item is None :
        raise HTTPException(status_code=404 , detail="Item not found")
    
    db_item.feedback = feedback.feedback
    db_item.is_error = feedback.is_error
    
    db.commit()
    db.refresh(db_item)
    return {"feedback": "Issue resolved successfully"}

@app.patch("/audit_Feedback/{product_code}")
def update_Feedback_audit(product_code: str ,db: Session = Depends(get_db)):
    db_item = db.query(CSVData).filter(CSVData.product_code == product_code).first()
    if db_item is None :
        raise HTTPException(status_code=404 , detail="Item not found")
    
    db_item.is_error = False
    db.commit()
    db.refresh(db_item)
    return {"feedback": "Issue resolved successfully"}

@app.patch("/branch_EditDetail/{product_code}")
def update_editDetail(product_code:str,edit_detail:Branch_EditDetail ,db: Session = Depends(get_db) ):
    db_item = db.query(CSVData).filter(CSVData.product_code == product_code).first()
    if db_item is None :
        raise HTTPException(status_code=404 , detail="Item not found")
    
    db_item.product_code = edit_detail.product_code
    db_item.branch_id = edit_detail.branch_id
    db_item.rec_type = edit_detail.rec_type
    db_item.doc_type = edit_detail.doc_type
    db_item.trans_type = edit_detail.trans_type
    db_item.doc_date = edit_detail.doc_date
    db_item.doc_no = edit_detail.doc_no
    db_item.reason_code = edit_detail.reason_code
    db_item.cv_code = edit_detail.cv_code
    db_item.pma_code = edit_detail.pma_code
    db_item.category_code = edit_detail.category_code
    db_item.subcategory_code = edit_detail.subcategory_code
    db_item.quantity = edit_detail.quantity
    
    db.commit()
    db.refresh(db_item)
    return {"status": "Edit Successfully"}