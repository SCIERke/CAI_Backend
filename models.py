from sqlalchemy import Boolean , Column , String ,Integer ,Float ,Date
from .database import Base

class CSVData(Base) :
    __tablename__ = "Anomalies"
    
    product_code = Column(String ,primary_key=True)
    branch_id = Column(String)
    area_code = Column(String)
    zone_id = Column(String)
    province_code = Column(String)
    rec_type = Column(String)
    doc_type = Column(String)
    trans_type = Column(String)
    doc_date = Column(String)
    doc_no = Column(String)
    reason_code = Column(String)
    cv_code = Column(String)
    pma_code = Column(String)
    category_code = Column(String)
    subcategory_code = Column(String)
    quantity = Column(Float)
    error_date = Column(String) # On-top in request process
    is_error = Column(Boolean)
    feedback = Column(String)
    # percent = Column(Float)

     