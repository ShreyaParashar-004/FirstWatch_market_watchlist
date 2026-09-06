from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User, WatchlistCompany, WatchlistTheme
from app.schemas import CompanyCreate, CompanyOut, ThemeCreate, ThemeOut

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


def _theme_out(row: WatchlistTheme) -> ThemeOut:
    keywords = [k.strip() for k in (row.keywords or "").split(",") if k.strip()]
    return ThemeOut(id=row.id, name=row.name, keywords=keywords, created_at=row.created_at)


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(WatchlistCompany)
        .filter(WatchlistCompany.user_id == user.id)
        .order_by(WatchlistCompany.created_at.asc())
        .all()
    )


@router.post("/companies", response_model=CompanyOut, status_code=201)
def add_company(body: CompanyCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticker = body.ticker.strip().upper()
    existing = (
        db.query(WatchlistCompany)
        .filter(WatchlistCompany.user_id == user.id, WatchlistCompany.ticker == ticker)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company already on watchlist")
    row = WatchlistCompany(user_id=user.id, ticker=ticker, name=body.name.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/companies/{company_id}", status_code=204)
def delete_company(company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = (
        db.query(WatchlistCompany)
        .filter(WatchlistCompany.id == company_id, WatchlistCompany.user_id == user.id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(row)
    db.commit()


@router.get("/themes", response_model=list[ThemeOut])
def list_themes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(WatchlistTheme)
        .filter(WatchlistTheme.user_id == user.id)
        .order_by(WatchlistTheme.created_at.asc())
        .all()
    )
    return [_theme_out(r) for r in rows]


@router.post("/themes", response_model=ThemeOut, status_code=201)
def add_theme(body: ThemeCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = body.name.strip()
    existing = (
        db.query(WatchlistTheme)
        .filter(WatchlistTheme.user_id == user.id, WatchlistTheme.name == name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Theme already on watchlist")
    keywords = ",".join(k.strip() for k in body.keywords if k.strip())
    row = WatchlistTheme(user_id=user.id, name=name, keywords=keywords)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _theme_out(row)


@router.delete("/themes/{theme_id}", status_code=204)
def delete_theme(theme_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = (
        db.query(WatchlistTheme)
        .filter(WatchlistTheme.id == theme_id, WatchlistTheme.user_id == user.id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Theme not found")
    db.delete(row)
    db.commit()
