import httpx
import time

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Service, MonitoringLog, User
from schemas import ServiceResponse, ServiceCreate, ServiceUpdate, MonitoringLogCreate, MonitoringLogResponse, UserCreate, UserResponse, UserLogin, TokenResponse
from security import hash_password, verify_password, create_access_token, get_current_user, require_admin

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Get the services
@app.get("/services", response_model=list[ServiceResponse])
@app.get("/services", response_model=list[ServiceResponse])
def get_services(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)):

    services = db.query(Service).all()
    return services

#create services
@app.post("/services", response_model=ServiceResponse)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    new_service = Service(
        name = service.name,
        endpoint = service.endpoint,
        method = service.method
    )

    try:
        db.add(new_service)
        db.commit()
        db.refresh(new_service)
    except Exception:
        db.rollback()
        raise

    return new_service

#update only the provided field
@app.patch("/services/{service_id}", response_model=ServiceResponse)
def update_service(service_id:int, service_update: ServiceUpdate, db:Session = Depends(get_db), current_user: dict = Depends(require_admin)):

    #1. Find the service
    service = db.query(Service).filter(Service.id == service_id).first()

    #2. If the service is not present then raise HTTPException error handling
    if service is None:
        raise HTTPException(
            status_code = 404,
            detail = "Service not found"
        )

    #3. Get only the fields which are provided by the client
    service_data = service_update.model_dump(exclude_unset=True)

    #4. Update those fields dynamically
    try:
        for field, value in service_data.items():
            setattr(service, field, value)

        #5. Save changes
        db.commit()

        #6. Refresh objects from database
        db.refresh(service)
    except Exception:
        db.rollback()
        raise

    #7. Return update service
    return service

@app.delete("/services/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_admin)):
    service = db.query(Service).filter(Service.id == service_id).first()

    if service is None:
        raise HTTPException(
            status_code = 404,
            detail = "Service not found"
        )
    
    try:
        db.delete(service)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message":"Service deleted successfully"
    }


@app.post("/services/{service_id}/logs", response_model=MonitoringLogResponse)
def create_monitoring_log(service_id: int, log: MonitoringLogCreate, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    new_log = MonitoringLog(
        service_id=service_id,
        status_code=log.status_code,
        response_time=log.response_time,
        is_healthy=log.is_healthy
    )

    try:
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
    except Exception:
        db.rollback()
        raise

    return new_log

@app.get("/services/{service_id}/logs", response_model=list[MonitoringLogResponse])
def get_monitoring_logs(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )
    
    log = db.query(MonitoringLog).filter(MonitoringLog.service_id == service_id).all()

    return log



# User create
@app.post("/auth/register", response_model=UserResponse)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.username == user.username
    ).first()

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    password_hash = hash_password(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=password_hash
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return new_user


@app.post("/auth/login", response_model=TokenResponse)
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.username == user.username
    ).first()

    if existing_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
        user.password,
        existing_user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        existing_user.username,
        existing_user.role
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/services/{service_id}/check")
def check_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    service = db.query(Service).filter(
        Service.id == service_id
    ).first()

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Service not found"
        )

    start_time = time.perf_counter()

    try:
        response = httpx.request(
            method=service.method,
            url=service.endpoint,
            timeout=5.0
        )

        end_time = time.perf_counter()

        response_time = round(
            (end_time - start_time) * 1000
        )

        is_healthy = 200 <= response.status_code < 400

        new_log = MonitoringLog(
            service_id=service.id,
            status_code=response.status_code,
            response_time=response_time,
            is_healthy=is_healthy
        )

        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        return {
            "service": service.name,
            "status_code": response.status_code,
            "response_time": response_time,
            "is_healthy": is_healthy
        }

    except Exception:
        end_time = time.perf_counter()

        response_time = round(
            (end_time - start_time) * 1000
        )

        new_log = MonitoringLog(
            service_id=service.id,
            status_code=0,
            response_time=response_time,
            is_healthy=False
        )

        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        return {
            "service": service.name,
            "status_code": 0,
            "response_time": response_time,
            "is_healthy": False
        }