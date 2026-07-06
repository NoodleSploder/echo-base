from __future__ import annotations

from dataclasses import asdict, replace

from fastapi import APIRouter, Depends, Response

from app.api.deps import (
    get_current_user,
    get_receiver_service,
    get_spectrum_scan_service,
    get_stream_service,
    get_triggered_recording_service,
    require_role,
)
from app.core.exceptions import ValidationAppError
from app.db.models.user import User, UserRole
from app.plugins.receiver import ReceiverStatus
from app.schemas.common import ok
from app.schemas.receiver import (
    BandwidthRequest,
    GainRequest,
    PpmCorrectionRequest,
    ReceiverDescriptorSchema,
    ReceiverLocationRequest,
    ReceiverStatusSchema,
    SampleRateRequest,
    ScanRequest,
    SignalDetectionRequest,
    TuneRequest,
)
from app.services.receiver_inventory import list_inventory, set_location
from app.services.receiver_service import ReceiverService
from app.services.signal_history import (
    DEFAULT_HISTORY_LIMIT,
    DEFAULT_HISTORY_MINUTES,
    query_signal_history,
)
from app.services.spectrum_scan import SpectrumScanService
from app.services.stream_service import StreamService
from app.services.triggered_recording import TriggeredRecordingService

router = APIRouter(prefix="/api/receivers", tags=["receivers"])

require_operator = require_role(UserRole.ADMINISTRATOR, UserRole.OPERATOR)


def _status_response(status: ReceiverStatus, receiver_id: str, stream_service: StreamService) -> dict:
    # `status.state` is a manual flag toggled by start()/stop() -- it
    # doesn't know whether a spectrum/audio subscriber has actually
    # triggered a live IQ capture. Report "streaming" whenever one has,
    # even if the receiver was never explicitly start()ed, so the UI
    # reflects real hardware activity rather than just the button state.
    if status.state == "idle" and stream_service.is_active(receiver_id):
        status = replace(status, state="streaming")
    return ok(ReceiverStatusSchema(**asdict(status)).model_dump())


@router.get("")
async def list_receivers(
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(get_current_user),
) -> dict:
    receivers = await service.list_receivers()
    return ok([ReceiverDescriptorSchema(**asdict(r)).model_dump() for r in receivers])


@router.post("/discover")
async def discover_receivers(
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(require_operator),
) -> dict:
    receivers = await service.discover()
    return ok([ReceiverDescriptorSchema(**asdict(r)).model_dump() for r in receivers])


@router.get("/inventory")
async def get_receiver_inventory(
    service: ReceiverService = Depends(get_receiver_service),
    _: User = Depends(get_current_user),
) -> dict:
    """Every receiver ever seen (survives both unplugging and a backend
    restart), each flagged with whether it's currently attached --
    distinct from `GET /api/receivers`, which only ever shows what's
    live right now. `attached` is computed from a fresh discovery at
    request time, not from `HotplugMonitor`'s own (up-to-10s-stale)
    last poll."""
    currently_attached = {d.id for d in await service.list_receivers()}
    records = await list_inventory()
    return ok(
        [
            {
                "receiver_id": r.receiver_id,
                "name": r.name,
                "driver": r.driver,
                "serial": r.serial,
                "first_seen_at": r.first_seen_at.isoformat(),
                "last_seen_at": r.last_seen_at.isoformat(),
                "attached": r.receiver_id in currently_attached,
                "site_name": r.site_name,
                "latitude": r.latitude,
                "longitude": r.longitude,
            }
            for r in records
        ]
    )


@router.put("/{receiver_id}/location")
async def put_receiver_location(
    receiver_id: str,
    payload: ReceiverLocationRequest,
    _: User = Depends(require_operator),
) -> dict:
    """Set this receiver's physical site location for the Geospatial
    Intelligence map's "Receiver Sites" layer -- operator-set, since a
    plain RTL-SDR dongle has no GPS of its own. Requires the receiver
    to already exist in inventory (i.e. have been seen at least once)."""
    record = await set_location(receiver_id, payload.latitude, payload.longitude, payload.site_name)
    return ok(
        {
            "receiver_id": record.receiver_id,
            "site_name": record.site_name,
            "latitude": record.latitude,
            "longitude": record.longitude,
        }
    )


@router.get("/{receiver_id}")
async def get_receiver(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(get_current_user),
) -> dict:
    status = await service.status(receiver_id)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/start")
async def start_receiver(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.start(receiver_id)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/stop")
async def stop_receiver(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.stop(receiver_id)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/tune")
async def tune_receiver(
    receiver_id: str,
    payload: TuneRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.tune(receiver_id, payload.frequency)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/gain")
async def set_gain(
    receiver_id: str,
    payload: GainRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.set_gain(receiver_id, payload.gain)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/bandwidth")
async def set_bandwidth(
    receiver_id: str,
    payload: BandwidthRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.set_bandwidth(receiver_id, payload.bandwidth)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/sample-rate")
async def set_sample_rate(
    receiver_id: str,
    payload: SampleRateRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.set_sample_rate(receiver_id, payload.sample_rate)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/ppm-correction")
async def set_ppm_correction(
    receiver_id: str,
    payload: PpmCorrectionRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    """Crystal oscillator frequency correction (parts per million) --
    takes effect on the receiver's *next* capture (tune/start/re-tune),
    not the one already running, same as gain/bandwidth/sample-rate."""
    status = await service.set_ppm_correction(receiver_id, payload.ppm)
    return _status_response(status, receiver_id, stream_service)


@router.post("/{receiver_id}/scan/start")
async def start_scan(
    receiver_id: str,
    payload: ScanRequest,
    service: ReceiverService = Depends(get_receiver_service),
    scan_service: SpectrumScanService = Depends(get_spectrum_scan_service),
    _: User = Depends(require_operator),
) -> dict:
    """Cycles the receiver through `frequencies` on a timer (`dwell_seconds`
    each), the same way the manual Tune button retunes it -- confirms the
    receiver exists first (raises ReceiverNotFoundError otherwise)."""
    await service.status(receiver_id)
    try:
        scan_service.start(receiver_id, payload.frequencies, payload.dwell_seconds)
    except ValueError as exc:
        raise ValidationAppError(str(exc)) from exc
    return ok({"message": "Scan started.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/scan/stop")
async def stop_scan(
    receiver_id: str,
    scan_service: SpectrumScanService = Depends(get_spectrum_scan_service),
    _: User = Depends(require_operator),
) -> dict:
    scan_service.stop(receiver_id)
    return ok({"message": "Scan stopped.", "receiver_id": receiver_id})


@router.get("/{receiver_id}/scan/status")
async def get_scan_status(
    receiver_id: str,
    scan_service: SpectrumScanService = Depends(get_spectrum_scan_service),
    _: User = Depends(get_current_user),
) -> dict:
    status = scan_service.status(receiver_id)
    return ok({"active": status is not None, **(status or {})})


@router.post("/{receiver_id}/aprs/start")
async def start_aprs_decoding(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    # Confirms the receiver exists (raises ReceiverNotFoundError otherwise)
    # before claiming hardware for it.
    await service.status(receiver_id)
    await stream_service.enable_aprs(receiver_id)
    return ok({"message": "APRS decoding enabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/aprs/stop")
async def stop_aprs_decoding(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await stream_service.disable_aprs(receiver_id)
    return ok({"message": "APRS decoding disabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/same/start")
async def start_same_decoding(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await service.status(receiver_id)
    await stream_service.enable_same(receiver_id)
    return ok({"message": "SAME decoding enabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/same/stop")
async def stop_same_decoding(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await stream_service.disable_same(receiver_id)
    return ok({"message": "SAME decoding disabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/ads-b/start")
async def start_ads_b_decoding(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    """Needs a genuinely wideband capture to decode anything real --
    tune to 1090000000 and `set_sample_rate` to at least 2000000 first
    (see `decoders/mode_s.py`'s docstring). Enabling it at the default
    240kHz spectrum/audio-oriented rate won't error, it just won't
    resolve any real Mode S pulses."""
    await service.status(receiver_id)
    await stream_service.enable_ads_b(receiver_id)
    return ok({"message": "ADS-B decoding enabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/ads-b/stop")
async def stop_ads_b_decoding(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await stream_service.disable_ads_b(receiver_id)
    return ok({"message": "ADS-B decoding disabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/ais/start")
async def start_ais_decoding(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await service.status(receiver_id)
    await stream_service.enable_ais(receiver_id)
    return ok({"message": "AIS decoding enabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/ais/stop")
async def stop_ais_decoding(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await stream_service.disable_ais(receiver_id)
    return ok({"message": "AIS decoding disabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/sstv/start")
async def start_sstv_decoding(
    receiver_id: str,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await service.status(receiver_id)
    await stream_service.enable_sstv(receiver_id)
    return ok({"message": "SSTV decoding enabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/sstv/stop")
async def stop_sstv_decoding(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await stream_service.disable_sstv(receiver_id)
    return ok({"message": "SSTV decoding disabled.", "receiver_id": receiver_id})


@router.get("/{receiver_id}/sstv")
async def get_sstv_snapshot(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(get_current_user),
) -> dict:
    snapshot = stream_service.get_sstv_snapshot(receiver_id)
    if snapshot is None:
        raise ValidationAppError(f"SSTV decoding is not enabled for '{receiver_id}'.")
    return ok(snapshot)


@router.get("/{receiver_id}/sstv/image.png")
async def get_sstv_image(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(get_current_user),
) -> Response:
    png_bytes = stream_service.get_sstv_image_png(receiver_id)
    if png_bytes is None:
        raise ValidationAppError(f"SSTV decoding is not enabled for '{receiver_id}'.")
    return Response(content=png_bytes, media_type="image/png")


@router.post("/{receiver_id}/signal-detection/start")
async def start_signal_detection(
    receiver_id: str,
    payload: SignalDetectionRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.status(receiver_id)  # raises ReceiverNotFoundError if unknown
    await stream_service.enable_signal_detection(receiver_id, payload.margin_db, status.frequency_hz)
    return ok({"message": "Signal detection enabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/signal-detection/stop")
async def stop_signal_detection(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await stream_service.disable_signal_detection(receiver_id)
    return ok({"message": "Signal detection disabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/occupancy/start")
async def start_occupancy(
    receiver_id: str,
    payload: SignalDetectionRequest,
    service: ReceiverService = Depends(get_receiver_service),
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    status = await service.status(receiver_id)  # raises ReceiverNotFoundError if unknown
    await stream_service.enable_occupancy(receiver_id, payload.margin_db, status.frequency_hz)
    return ok({"message": "Occupancy tracking enabled.", "receiver_id": receiver_id})


@router.post("/{receiver_id}/occupancy/stop")
async def stop_occupancy(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(require_operator),
) -> dict:
    await stream_service.disable_occupancy(receiver_id)
    return ok({"message": "Occupancy tracking disabled.", "receiver_id": receiver_id})


@router.get("/{receiver_id}/occupancy")
async def get_occupancy(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    _: User = Depends(get_current_user),
) -> dict:
    snapshot = stream_service.get_occupancy(receiver_id)
    if snapshot is None:
        raise ValidationAppError(f"Occupancy tracking is not enabled for '{receiver_id}'.")
    return ok(snapshot)


@router.get("/{receiver_id}/signal-history")
async def get_signal_history(
    receiver_id: str,
    minutes: int = DEFAULT_HISTORY_MINUTES,
    limit: int = DEFAULT_HISTORY_LIMIT,
    _: User = Depends(get_current_user),
) -> dict:
    records = await query_signal_history(receiver_id, minutes=minutes, limit=limit)
    return ok(
        [
            {
                "frequency_hz": r.frequency_hz,
                "frequency_offset_hz": r.frequency_offset_hz,
                "power_db": r.power_db,
                "detected_at": r.detected_at.isoformat(),
            }
            for r in records
        ]
    )


@router.get("/{receiver_id}/capture-health")
async def get_capture_health(
    receiver_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    triggered_recording_service: TriggeredRecordingService = Depends(get_triggered_recording_service),
    _: User = Depends(get_current_user),
) -> dict:
    """None/`active: false` if nobody's currently subscribed to anything
    for this receiver -- not an error, just "no capture running". Also
    carries `triggered_recording_armed` -- not itself a capture
    subscriber, but UI state a client needs to stay in sync with the
    backend the same way the decoder-enabled flags below do."""
    armed = triggered_recording_service.is_armed(receiver_id)
    health = stream_service.capture_health(receiver_id)
    if health is None:
        return ok({"active": False, "triggered_recording_armed": armed})
    return ok({"active": True, **health, "triggered_recording_armed": armed})
