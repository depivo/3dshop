import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.auth import require_admin
from app.config import settings
from app.database import get_db
from app.models import Order, OrderFile, OrderStatus
from app.schemas import OrderCreated, OrderOut, OrderUpdate
from app.telegram import notify_new_order

router = APIRouter()

ALLOWED_EXTENSIONS = {".stl", ".3mf"}


async def _save_upload(order_dir: Path, upload: UploadFile) -> tuple[str, int]:
    original_name = upload.filename or "model"
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл «{original_name}»: дозволені лише .stl і .3mf",
        )

    order_dir.mkdir(parents=True, exist_ok=True)
    dest_path = order_dir / f"{uuid.uuid4().hex}_{original_name}"

    size = 0
    chunk_size = 1024 * 1024
    with dest_path.open("wb") as f:
        while chunk := await upload.read(chunk_size):
            size += len(chunk)
            if size > settings.max_upload_size_bytes:
                f.close()
                dest_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Файл «{original_name}» занадто великий",
                )
            f.write(chunk)

    if size == 0:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Файл «{original_name}» порожній"
        )

    return str(dest_path), size


def _with_files(query):
    return query.options(joinedload(Order.files))


@router.post("/orders", response_model=OrderCreated, status_code=status.HTTP_201_CREATED)
async def create_order(
    name: str = Form(...),
    phone: str = Form(...),
    comment: str | None = Form(None),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> Order:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Додайте хоча б один файл")

    order_id = uuid.uuid4().hex
    order_dir = settings.uploads_dir / order_id

    order_files = []
    for upload in files:
        stored_path, size = await _save_upload(order_dir, upload)
        order_files.append(
            OrderFile(
                original_filename=upload.filename or "model",
                stored_path=stored_path,
                file_size=size,
            )
        )

    order = Order(
        id=order_id,
        name=name.strip(),
        phone=phone.strip(),
        comment=comment.strip() if comment else None,
        files=order_files,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    await notify_new_order(order)

    return order


@router.get("/admin/orders", response_model=list[OrderOut], dependencies=[Depends(require_admin)])
def list_orders(status_filter: OrderStatus | None = None, db: Session = Depends(get_db)):
    query = _with_files(db.query(Order)).order_by(Order.created_at.desc())
    if status_filter is not None:
        query = query.filter(Order.status == status_filter)
    return query.all()


@router.get(
    "/admin/orders/{order_id}", response_model=OrderOut, dependencies=[Depends(require_admin)]
)
def get_order(order_id: str, db: Session = Depends(get_db)) -> Order:
    order = _with_files(db.query(Order)).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Замовлення не знайдено")
    return order


@router.patch(
    "/admin/orders/{order_id}", response_model=OrderOut, dependencies=[Depends(require_admin)]
)
def update_order(order_id: str, payload: OrderUpdate, db: Session = Depends(get_db)) -> Order:
    order = _with_files(db.query(Order)).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Замовлення не знайдено")

    if payload.status is not None:
        order.status = payload.status
    if payload.price is not None:
        order.price = payload.price

    db.commit()
    db.refresh(order)
    return order


@router.get(
    "/admin/orders/{order_id}/files/{file_id}", dependencies=[Depends(require_admin)]
)
def download_order_file(order_id: str, file_id: str, db: Session = Depends(get_db)) -> FileResponse:
    order_file = (
        db.query(OrderFile)
        .filter(OrderFile.id == file_id, OrderFile.order_id == order_id)
        .first()
    )
    if order_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не знайдено")

    path = Path(order_file.stored_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не знайдено")

    return FileResponse(path, filename=order_file.original_filename)
