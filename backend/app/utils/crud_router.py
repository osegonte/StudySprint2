# backend/app/utils/crud_router.py
"""Generic CRUD Router Factory - Powers all standard endpoints with minimal boilerplate"""

from typing import Type, TypeVar, Generic, Optional, List, Any, Dict, Callable
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID

from app.config.database import get_db
from app.api.v1.auth import get_current_user
from studysprint_db.models.user import User

# Type variables for generic CRUD
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)

class CRUDService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic CRUD service class that all services inherit from"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def create(self, db: Session, *, obj_in: CreateSchemaType, user_id: str, **kwargs) -> ModelType:
        """Create a new object"""
        obj_data = obj_in.dict()
        obj_data["user_id"] = user_id
        obj_data.update(kwargs)
        
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, id: UUID, user_id: str) -> Optional[ModelType]:
        """Get object by ID (with user ownership check)"""
        return db.query(self.model).filter(
            self.model.id == id,
            self.model.user_id == user_id,
            self.model.is_deleted == False
        ).first()
    
    def get_multi(
        self,
        db: Session,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        filters: Dict[str, Any] = None
    ) -> List[ModelType]:
        """Get multiple objects with pagination and filtering"""
        query = db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.is_deleted == False
        )
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        **kwargs
    ) -> ModelType:
        """Update an object"""
        obj_data = obj_in.dict(exclude_unset=True)
        obj_data.update(kwargs)
        
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: UUID, user_id: str) -> bool:
        """Soft delete an object"""
        obj = self.get(db, id=id, user_id=user_id)
        if obj:
            obj.is_deleted = True
            db.commit()
            return True
        return False
    
    def count(self, db: Session, user_id: str, filters: Dict[str, Any] = None) -> int:
        """Count objects with optional filters"""
        query = db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.is_deleted == False
        )
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()

def create_crud_router(
    model: Type[ModelType],
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    response_schema: Type[ResponseSchemaType],
    service_class: Type[CRUDService] = None,
    prefix: str = "",
    tags: List[str] = None,
    create_dependencies: List[Callable] = None,
    update_dependencies: List[Callable] = None,
    delete_dependencies: List[Callable] = None,
    custom_endpoints: Dict[str, Callable] = None
) -> APIRouter:
    """
    Factory function to create CRUD router with all standard endpoints
    
    Args:
        model: SQLAlchemy model class
        create_schema: Pydantic schema for creation
        update_schema: Pydantic schema for updates
        response_schema: Pydantic schema for responses
        service_class: Custom service class (defaults to CRUDService)
        prefix: Router prefix
        tags: OpenAPI tags
        create_dependencies: Additional dependencies for create endpoint
        update_dependencies: Additional dependencies for update endpoint
        delete_dependencies: Additional dependencies for delete endpoint
        custom_endpoints: Additional custom endpoints {method_path: handler}
    """
    
    router = APIRouter(prefix=prefix, tags=tags or [])
    
    # Initialize service
    if service_class:
        service = service_class(model)
    else:
        service = CRUDService(model)
    
    # Dependency helpers
    def get_object_or_404(item_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        """Get object by ID or raise 404"""
        obj = service.get(db, id=item_id, user_id=str(current_user.id))
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found"
            )
        return obj
    
    # CREATE endpoint
    @router.post("/", response_model=response_schema, status_code=status.HTTP_201_CREATED)
    async def create_item(
        item_in: create_schema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        **additional_deps
    ):
        """Create new item"""
        try:
            item = service.create(db=db, obj_in=item_in, user_id=str(current_user.id))
            return response_schema.from_orm(item)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Creation failed: {str(e)}"
            )
    
    # Apply additional create dependencies
    if create_dependencies:
        for dep in create_dependencies:
            create_item = Depends(dep)(create_item)
    
    # READ (multiple) endpoint
    @router.get("/", response_model=List[response_schema])
    async def get_items(
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        """Get multiple items with pagination"""
        items = service.get_multi(db=db, user_id=str(current_user.id), skip=skip, limit=limit)
        return [response_schema.from_orm(item) for item in items]
    
    # READ (single) endpoint
    @router.get("/{item_id}", response_model=response_schema)
    async def get_item(item = Depends(get_object_or_404)):
        """Get single item by ID"""
        return response_schema.from_orm(item)
    
    # UPDATE endpoint
    @router.put("/{item_id}", response_model=response_schema)
    async def update_item(
        item_in: update_schema,
        item = Depends(get_object_or_404),
        db: Session = Depends(get_db),
        **additional_deps
    ):
        """Update item"""
        try:
            updated_item = service.update(db=db, db_obj=item, obj_in=item_in)
            return response_schema.from_orm(updated_item)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Update failed: {str(e)}"
            )
    
    # Apply additional update dependencies
    if update_dependencies:
        for dep in update_dependencies:
            update_item = Depends(dep)(update_item)
    
    # DELETE endpoint
    @router.delete("/{item_id}")
    async def delete_item(
        item_id: UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        **additional_deps
    ):
        """Delete item"""
        success = service.delete(db=db, id=item_id, user_id=str(current_user.id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found"
            )
        return {"message": f"{model.__name__} deleted successfully"}
    
    # Apply additional delete dependencies
    if delete_dependencies:
        for dep in delete_dependencies:
            delete_item = Depends(dep)(delete_item)
    
    # COUNT endpoint
    @router.get("/count/total")
    async def count_items(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        """Get total count of items"""
        count = service.count(db=db, user_id=str(current_user.id))
        return {"total": count}
    
    # SEARCH endpoint (if model has searchable fields)
    if hasattr(model, 'name') or hasattr(model, 'title'):
        @router.get("/search/{query}")
        async def search_items(
            query: str,
            skip: int = Query(0, ge=0),
            limit: int = Query(50, ge=1, le=200),
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            """Search items by name/title"""
            search_field = 'name' if hasattr(model, 'name') else 'title'
            items = db.query(model).filter(
                model.user_id == current_user.id,
                model.is_deleted == False,
                getattr(model, search_field).ilike(f"%{query}%")
            ).offset(skip).limit(limit).all()
            
            return [response_schema.from_orm(item) for item in items]
    
    # Add custom endpoints
    if custom_endpoints:
        for method_path, handler in custom_endpoints.items():
            method, path = method_path.split(' ', 1)
            router.add_api_route(path, handler, methods=[method.upper()])
    
    # Health check endpoint
    @router.get("/health/status")
    async def service_health():
        """Health check for this service"""
        return {
            "status": "healthy",
            "service": model.__tablename__,
            "endpoints": ["create", "read", "update", "delete", "count", "search"]
        }
    
    return router

# Specialized CRUD service classes for different domains
class TopicCRUDService(CRUDService):
    """Extended CRUD service for Topics with statistics"""
    
    def create(self, db: Session, *, obj_in: CreateSchemaType, user_id: str, **kwargs) -> ModelType:
        """Create topic and update user statistics"""
        topic = super().create(db, obj_in=obj_in, user_id=user_id, **kwargs)
        
        # Update user topic count
        from studysprint_db.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.total_pdfs += 0  # Will be updated when PDFs are added
            db.commit()
        
        return topic
    
    def get_with_stats(self, db: Session, id: UUID, user_id: str) -> Optional[Dict[str, Any]]:
        """Get topic with calculated statistics"""
        topic = self.get(db, id=id, user_id=user_id)
        if not topic:
            return None
        
        # Calculate stats (will implement when PDF model exists)
        stats = {
            "total_pdfs": 0,
            "total_pages": 0,
            "study_time_minutes": 0,
            "completion_percentage": 0.0,
            "last_studied": None
        }
        
        return {
            "topic": topic,
            "statistics": stats
        }

class PDFCRUDService(CRUDService):
    """Extended CRUD service for PDFs with file handling"""
    
    def create_with_file(self, db: Session, *, obj_in: CreateSchemaType, user_id: str, file_path: str, **kwargs) -> ModelType:
        """Create PDF with file handling"""
        import os
        from PyPDF2 import PdfReader
        
        # Extract PDF metadata
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                page_count = len(pdf_reader.pages)
                file_size = os.path.getsize(file_path)
        except Exception:
            page_count = 0
            file_size = 0
        
        # Create PDF record
        pdf_data = obj_in.dict()
        pdf_data.update({
            "user_id": user_id,
            "file_path": file_path,
            "file_size": file_size,
            "total_pages": page_count,
            **kwargs
        })
        
        pdf = self.model(**pdf_data)
        db.add(pdf)
        db.commit()
        db.refresh(pdf)
        
        return pdf

# Pre-configured router factory functions for common patterns
def create_user_owned_crud_router(
    model: Type[ModelType],
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    response_schema: Type[ResponseSchemaType],
    name: str,
    service_class: Type[CRUDService] = None
) -> APIRouter:
    """Create CRUD router for user-owned resources"""
    return create_crud_router(
        model=model,
        create_schema=create_schema,
        update_schema=update_schema,
        response_schema=response_schema,
        service_class=service_class,
        prefix=f"/{name}",
        tags=[name.title()]
    )

def create_nested_crud_router(
    model: Type[ModelType],
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    response_schema: Type[ResponseSchemaType],
    parent_name: str,
    child_name: str,
    service_class: Type[CRUDService] = None
) -> APIRouter:
    """Create CRUD router for nested resources (e.g., /topics/{topic_id}/pdfs)"""
    return create_crud_router(
        model=model,
        create_schema=create_schema,
        update_schema=update_schema,
        response_schema=response_schema,
        service_class=service_class,
        prefix=f"/{parent_name}/{{parent_id}}/{child_name}",
        tags=[f"{parent_name.title()} {child_name.title()}"]
    )