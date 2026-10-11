from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.transactions import Transaction

def handle_get_movement_percentage(db: Session) -> dict:

    stmt = (
        select(
            func.count(Transaction.id).label("whole"),
            
            func.count(Transaction.id)
            .filter(Transaction.transaction_type == "stock in")
            .label("in_part"),

            func.count(Transaction.id)
            .filter(Transaction.transaction_type == "stock out")
            .label("out_part")
        )
    )

    row = db.execute(stmt).first()

    if row is not None:
        whole = row.whole
        in_part = row.in_part
        out_part = row.out_part
    else:
        whole, in_part, out_part = 0, 0, 0

    total_transaction = whole

    if total_transaction == 0:
        return {
            "transaction_count": 0,
            "stock_in_percentage": 0,
            "stock_out_percentage": 0
        }

    in_percentage = (in_part / whole) * 100
    out_percentage = (out_part / whole) * 100

    return {
        "transaction_count": total_transaction,
        "stock_in_percentage": in_percentage,
        "stock_out_percentage": out_percentage
    }