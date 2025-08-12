from pydantic import BaseModel


class TripSchema(BaseModel):
    class Config:
        from_attributes = True

    # vendor_id: int
    # passenger_count: int
    # trip_distance: float
    # duration_minutes: float
    # amount: float
    # payment_type: str
    # fare_amount: float
    # extra: float
    # mta_tax: float
