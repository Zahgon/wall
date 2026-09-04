"""HTTP routes for the ads app."""

from __future__ import annotations

from fastapi import APIRouter, Response
from sqlalchemy import select
from starlette.datastructures import UploadFile
from starlette.requests import Request

from ads.models import Ad
from ads.pagination import StandardResultsSetPagination
from ads.schemas import AdSchema, AdWrite, PaginatedAds
from ads.storage import delete_image, save_image
from wall.dependencies import CurrentUser, DatabaseSession
from wall.exceptions import NOT_FOUND, NotFound
from wall.parsers import parse_multipart
from wall.validation import validate

router = APIRouter()

paginator = StandardResultsSetPagination()


def _lookup(session: DatabaseSession, pk: str) -> Ad:
    """Resolve a primary key the way the original integer route did.

    A non-numeric segment never matched the route at all, so it is a 404 rather
    than a validation error, and a missing row is a 404 as well.
    """
    if not pk.isdigit():
        raise NotFound(NOT_FOUND)
    ad = session.get(Ad, int(pk))
    if ad is None:
        raise NotFound(NOT_FOUND)
    return ad


async def _write_fields(request: Request, ad: Ad) -> str:
    """Apply the writable part of a multipart payload onto ``ad``.

    Returns the name of the stored file the write superseded (empty when no
    replacement happened) so the caller can remove it once the write is
    committed -- files are only deleted after the database change succeeds.
    """
    form = await parse_multipart(request)
    payload = validate(AdWrite, form)
    ad.title = payload.title
    ad.caption = payload.caption

    upload = form.get("image")
    if isinstance(upload, UploadFile) and upload.filename:
        replaced = ad.image
        ad.image = save_image(upload)
        return replaced
    return ""


@router.get("/all", name="ad_list", response_model=PaginatedAds)
async def ad_list(request: Request, session: DatabaseSession) -> PaginatedAds:
    """List public ads, newest first, one per page unless asked otherwise."""
    statement = select(Ad).where(Ad.is_public.is_(True)).order_by(Ad.date_added.desc())
    ads = session.scalars(statement).all()
    page = paginator.paginate(ads, request)
    return PaginatedAds(
        count=page.count,
        next=page.next,
        previous=page.previous,
        results=[AdSchema.from_ad(ad) for ad in page.objects],
    )


@router.post("/add", name="ad_create", response_model=AdSchema)
async def ad_create(request: Request, session: DatabaseSession, user: CurrentUser) -> AdSchema:
    """Publish an ad on behalf of the caller, answering 200 as before."""
    ad = Ad(publisher=user)
    await _write_fields(request, ad)
    session.add(ad)
    session.commit()
    session.refresh(ad)
    return AdSchema.from_ad(ad)


@router.api_route("/{pk}", methods=["GET", "PUT", "DELETE"], name="ad_detail", response_model=None)
async def ad_detail(
    request: Request,
    pk: str,
    session: DatabaseSession,
    user: CurrentUser,
) -> AdSchema | Response:
    """Read, replace or remove a single ad.

    Ownership is not enforced: the original permission class only declared an
    object-level hook, and no view ever asked for that check to run.
    """
    ad = _lookup(session, pk)

    if request.method == "DELETE":
        stored = ad.image
        session.delete(ad)
        session.commit()
        delete_image(stored)
        return Response(status_code=204)

    if request.method == "PUT":
        replaced = await _write_fields(request, ad)
        session.commit()
        session.refresh(ad)
        delete_image(replaced)

    return AdSchema.from_ad(ad)
