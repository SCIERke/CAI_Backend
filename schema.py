from pydantic import BaseModel

# Base
class ItemBase(BaseModel) :
    title: str
    description : str
    price : float

# Request ถ้าอนาคตจะมาแก้ก่อนเข้า ORM ก็แก้ตรงนี้
class ItemCreated(ItemBase):
    pass

# Response
class ItemResponse(ItemBase):
    id: int
    class Config:
        from_attributes = True #ORM mode
        
class AnomaliesLists_Branch(BaseModel):
    product_code: str
    error_date: str
    
class AnomaliesDetail_Branch(BaseModel):
    product_code: str
    branch_id: str
    area_code: str
    zone_id: str
    province_code: str
    rec_type: str
    doc_type: str
    trans_type: str
    doc_date: str
    doc_no: str
    reason_code: str
    cv_code: str
    pma_code: str
    category_code: str
    subcategory_code: str
    quantity: float
    error_date: str
    is_error: bool
    feedback: str
    
class Branch_Feedback_Resolve(BaseModel):
    feedback: str
    is_error: bool

class Branch_EditDetail(BaseModel):
    product_code: str
    branch_id: str
    rec_type: str
    doc_type: str
    trans_type: str
    doc_date: str
    doc_no: str
    reason_code: str
    cv_code: str
    pma_code: str
    category_code: str
    subcategory_code: str
    quantity: float