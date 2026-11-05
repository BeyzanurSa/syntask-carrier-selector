from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import SessionDep
from app.database.models import Carrier
from app.schemas.carrier import CarrierIn, CarrierOut
from app.services import carriers as service

router = APIRouter(prefix="/carriers", tags=["carriers"])

NOT_FOUND = HTTPException(status_code=404, detail="Taşıyıcı bulunamadı")


def _duplicate(name: str) -> HTTPException:
    return HTTPException(status_code=409, detail=f"'{name}' adında bir taşıyıcı zaten var")


@router.get("", response_model=list[CarrierOut])
def list_carriers(session: SessionDep) -> list[Carrier]:
    return service.list_carriers(session)


@router.post("", response_model=CarrierOut, status_code=status.HTTP_201_CREATED)
def create_carrier(data: CarrierIn, session: SessionDep) -> Carrier:
    try:
        return service.create_carrier(session, data)
    except service.DuplicateCarrierName:
        raise _duplicate(data.name) from None


@router.get("/{carrier_id}", response_model=CarrierOut)
def get_carrier(carrier_id: int, session: SessionDep) -> Carrier:
    try:
        return service.get_carrier(session, carrier_id)
    except service.CarrierNotFound:
        raise NOT_FOUND from None


@router.put("/{carrier_id}", response_model=CarrierOut)
def replace_carrier(carrier_id: int, data: CarrierIn, session: SessionDep) -> Carrier:
    try:
        return service.replace_carrier(session, carrier_id, data)
    except service.CarrierNotFound:
        raise NOT_FOUND from None
    except service.DuplicateCarrierName:
        raise _duplicate(data.name) from None


@router.delete("/{carrier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_carrier(carrier_id: int, session: SessionDep) -> Response:
    try:
        service.delete_carrier(session, carrier_id)
    except service.CarrierNotFound:
        raise NOT_FOUND from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
