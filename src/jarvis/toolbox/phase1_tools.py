"""The six initial approved tools (PRD section 21, "Initial approved tools").

Open an approved app · open an approved website · media control · volume
control · speak · notify.

Every one is a narrow typed tool with its own catalogue capability and risk
level. None of them widens an existing tool, and none of them takes free text
where a typed value would do — the model chooses *which catalogue entry*, never
*which binary* (ADR-0029 constraint 3).

`succeeded` requires verification throughout. A launch that could not be
confirmed is `succeeded` + `unverified`, which does not satisfy a task's success
criteria (PRD FR-048, AT-018).
"""

from __future__ import annotations

import logging
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field

from jarvis.core.permissions.models import RiskLevel
from jarvis.core.tools.contract import (
    RetryPolicy,
    ToolContext,
    ToolExecution,
    ToolFailure,
    ToolSpec,
    Verification,
)
from jarvis.toolbox.launch import (
    ApplicationCatalogue,
    ArgumentKind,
    CatalogueError,
    LaunchKind,
    launch,
)
from jarvis.toolbox.media import MediaAction, VolumeAction, media_available, send_media_key

__all__ = [
    "OpenApplicationTool",
    "OpenUrlTool",
    "WebSearchTool",
    "SEARCH_ENGINES",
    "MediaControlTool",
    "VolumeControlTool",
    "SpeakTool",
    "NotifyTool",
    "register_phase1_tools",
]

_LOG = logging.getLogger(__name__)


# =========================================================================
# Open an approved application
# =========================================================================
class OpenApplicationInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    application: str = Field(
        description="The catalogue id, name or alias of an approved application."
    )
    argument: str | None = Field(
        default=None,
        description="Only where the entry declares one, such as a Steam app id.",
    )


class OpenApplicationOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    application: str
    started: bool
    verified: bool
    pid: int | None = None
    detail: str


class OpenApplicationTool:
    """Launch a catalogued application and verify it started (FR-063, FR-064)."""

    spec = ToolSpec(
        tool_id="app.open",
        version="1.0.0",
        description="Open an application the user has already approved.",
        input_model=OpenApplicationInput,
        output_model=OpenApplicationOutput,
        risk=RiskLevel.LOW,
        required_capabilities=("app.open_approved",),
        resource_locks=(),
        timeout_seconds=30.0,
        retry_policy=RetryPolicy(max_attempts=1),
        changes_state=True,
        verification="Confirms the application's process is running before reporting success.",
        failure_codes=("unknown_application", "launch_refused", "launch_failed"),
        target_parameter="application",
        reversible=True,
    )

    def __init__(self, catalogue: ApplicationCatalogue) -> None:
        self._catalogue = catalogue

    def run(self, context: ToolContext, parameters: BaseModel) -> ToolExecution:
        assert isinstance(parameters, OpenApplicationInput)
        entry = self._catalogue.resolve(parameters.application)
        if entry is None:
            raise ToolFailure(
                "unknown_application",
                f"'{parameters.application}' is not in the approved application "
                f"catalogue, so it cannot be opened. Approved: "
                f"{', '.join(self._catalogue.ids()) or 'none'}. "
                "There is no way to add an application from inside Jarvis in "
                "this build — do not tell the user to look for one. Adding an "
                "application is a change only the owner can make to the "
                "catalogue itself.",
            )
        try:
            outcome = launch(entry, parameters.argument)
        except CatalogueError as exc:
            raise ToolFailure("launch_refused", str(exc)) from exc
        except OSError as exc:
            raise ToolFailure(
                "launch_failed", f"could not start {entry.display_name}: {exc}"
            ) from exc

        return ToolExecution(
            output=OpenApplicationOutput(
                application=entry.display_name,
                started=outcome.started,
                verified=outcome.verified,
                pid=outcome.pid,
                detail=outcome.detail,
            ),
            # The distinction that matters: launched is not the same as running.
            verification=Verification.VERIFIED if outcome.verified else Verification.UNVERIFIED,
            message=outcome.detail,
            evidence={"argv": list(outcome.argv)},
        )


# =========================================================================
# Open an approved website
# =========================================================================
class OpenUrlInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str = Field(description="An http or https URL.")


class OpenUrlOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str
    host: str
    started: bool
    verified: bool
    detail: str


class OpenUrlTool:
    """Open a URL in the approved browser. Scheme-restricted (ADR-0029)."""

    spec = ToolSpec(
        tool_id="web.open_url",
        version="1.0.0",
        description="Open a web page in the approved browser.",
        input_model=OpenUrlInput,
        output_model=OpenUrlOutput,
        risk=RiskLevel.LOW,
        required_capabilities=("web.open_approved_url",),
        resource_locks=(),
        timeout_seconds=30.0,
        retry_policy=RetryPolicy(max_attempts=1),
        changes_state=True,
        verification="Confirms the browser process is running before reporting success.",
        failure_codes=("no_browser", "refused_url", "launch_failed"),
        target_parameter="url",
        reversible=True,
    )

    def __init__(self, catalogue: ApplicationCatalogue, browser_id: str = "brave") -> None:
        self._catalogue = catalogue
        self._browser_id = browser_id

    def run(self, context: ToolContext, parameters: BaseModel) -> ToolExecution:
        assert isinstance(parameters, OpenUrlInput)
        from urllib.parse import urlparse

        entry = self._catalogue.get(self._browser_id)
        if entry is None:
            raise ToolFailure(
                "no_browser",
                f"'{self._browser_id}' is not in the application catalogue, so "
                "there is no approved browser to open a page in.",
            )
        try:
            outcome = launch(entry, parameters.url)
        except CatalogueError as exc:
            # The scheme check lives in the launcher, so it holds for every
            # caller rather than only for this tool.
            raise ToolFailure("refused_url", str(exc)) from exc
        except OSError as exc:
            raise ToolFailure("launch_failed", str(exc)) from exc

        return ToolExecution(
            output=OpenUrlOutput(
                url=parameters.url,
                host=urlparse(parameters.url).netloc,
                started=outcome.started,
                verified=outcome.verified,
                detail=outcome.detail,
            ),
            verification=Verification.VERIFIED if outcome.verified else Verification.UNVERIFIED,
            message=outcome.detail,
            evidence={"argv": list(outcome.argv)},
        )


# =========================================================================
# Web search
# =========================================================================
#: Search engines Jarvis will build a query for. A closed table, so the model
#: chooses *which approved engine*, never a URL — the same rule the application
#: catalogue applies to executables (ADR-0029 constraint 3).
SEARCH_ENGINES: dict[str, str] = {
    "google": "https://www.google.com/search?q={query}",
    "duckduckgo": "https://duckduckgo.com/?q={query}",
    "youtube": "https://www.youtube.com/results?search_query={query}",
}

DEFAULT_SEARCH_ENGINE = "duckduckgo"


class WebSearchInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str = Field(
        min_length=1,
        max_length=400,
        description="What to search for, in plain words. Not a URL.",
    )
    engine: str = Field(
        default=DEFAULT_SEARCH_ENGINE,
        description=f"One of: {', '.join(sorted(SEARCH_ENGINES))}.",
    )


class WebSearchOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    query: str
    engine: str
    url: str
    started: bool
    verified: bool
    detail: str


class WebSearchTool:
    """Search the web for a phrase, in the approved browser.

    Exists because asking the model for a URL produced malformed ones. A real
    example that reached the user as a Google 400 page:

        https://www.google.com/search?q=latest%2Bupcoming%2Bvideogames+%3A2027&tbm=news

    The model had percent-encoded its own separators. Taking the words and
    building the URL here removes the whole class of error: there is exactly
    one place that knows how to encode a query, and it is not the model.
    """

    spec = ToolSpec(
        tool_id="web.search",
        version="1.0.0",
        description=(
            "Search the web for a phrase and open the results in the approved "
            "browser. Give plain words — never a URL, and never pre-encoded text."
        ),
        input_model=WebSearchInput,
        output_model=WebSearchOutput,
        risk=RiskLevel.LOW,
        required_capabilities=("web.open_approved_url",),
        resource_locks=(),
        timeout_seconds=30.0,
        retry_policy=RetryPolicy(max_attempts=1),
        changes_state=True,
        verification="Confirms the browser process is running before reporting success.",
        failure_codes=("no_browser", "unknown_engine", "refused_url", "launch_failed"),
        target_parameter="query",
        reversible=True,
    )

    def __init__(self, catalogue: ApplicationCatalogue, browser_id: str = "brave") -> None:
        self._catalogue = catalogue
        self._browser_id = browser_id

    def run(self, context: ToolContext, parameters: BaseModel) -> ToolExecution:
        assert isinstance(parameters, WebSearchInput)
        from urllib.parse import quote_plus

        engine = parameters.engine.strip().lower()
        template = SEARCH_ENGINES.get(engine)
        if template is None:
            raise ToolFailure(
                "unknown_engine",
                f"'{parameters.engine}' is not a search engine Jarvis knows. "
                f"Use one of: {', '.join(sorted(SEARCH_ENGINES))}.",
            )

        entry = self._catalogue.get(self._browser_id)
        if entry is None:
            raise ToolFailure(
                "no_browser",
                f"'{self._browser_id}' is not in the application catalogue, so "
                "there is no approved browser to search in.",
            )

        # One encoding, done once, by code that knows the rules.
        url = template.format(query=quote_plus(parameters.query.strip()))
        try:
            outcome = launch(entry, url)
        except CatalogueError as exc:
            raise ToolFailure("refused_url", str(exc)) from exc
        except OSError as exc:
            raise ToolFailure("launch_failed", str(exc)) from exc

        return ToolExecution(
            output=WebSearchOutput(
                query=parameters.query,
                engine=engine,
                url=url,
                started=outcome.started,
                verified=outcome.verified,
                detail=outcome.detail,
            ),
            verification=Verification.VERIFIED if outcome.verified else Verification.UNVERIFIED,
            message=(
                f"Searched {engine} for '{parameters.query}'. {outcome.detail} "
                "Jarvis cannot read the results — they are on your screen, not "
                "available to it."
            ),
            evidence={"argv": list(outcome.argv), "url": url},
        )


# =========================================================================
# Media control
# =========================================================================
class MediaControlInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    action: MediaAction = Field(description="play_pause, next, previous or stop.")


class MediaControlOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    action: str
    sent: bool
    detail: str


class MediaControlTool:
    """Send a system media key. A closed set of actions, never a key code."""

    spec = ToolSpec(
        tool_id="media.control",
        version="1.0.0",
        description="Play, pause, skip or stop whatever is currently playing.",
        input_model=MediaControlInput,
        output_model=MediaControlOutput,
        risk=RiskLevel.LOW,
        required_capabilities=("media.playback_control",),
        resource_locks=(),
        timeout_seconds=5.0,
        retry_policy=RetryPolicy(max_attempts=1),
        changes_state=True,
        verification=(
            "Reports whether Windows accepted the key. Whether an application "
            "acted on it cannot be observed from here, so this is unverified."
        ),
        failure_codes=("unavailable", "rejected"),
        reversible=True,
    )

    def run(self, context: ToolContext, parameters: BaseModel) -> ToolExecution:
        assert isinstance(parameters, MediaControlInput)
        if not media_available():
            raise ToolFailure(
                "unavailable", "media keys are a Windows facility and are not available here"
            )
        sent = send_media_key(parameters.action.value)
        if not sent:
            raise ToolFailure("rejected", "Windows did not accept the media key")
        return ToolExecution(
            output=MediaControlOutput(
                action=parameters.action.value,
                sent=True,
                detail=f"sent {parameters.action.value}",
            ),
            # Honest: the key went to the system. Whether Spotify was listening
            # is not something this tool can see.
            verification=Verification.UNVERIFIED,
            message=(
                f"Sent {parameters.action.value}. Whether the playing application "
                "acted on it cannot be confirmed from here."
            ),
        )


# =========================================================================
# Volume control
# =========================================================================
class VolumeControlInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    action: VolumeAction = Field(description="mute, volume_up or volume_down.")
    steps: int = Field(default=1, ge=1, le=10, description="How many increments.")


class VolumeControlOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    action: str
    steps: int
    sent: bool


class VolumeControlTool:
    spec = ToolSpec(
        tool_id="device.volume",
        version="1.0.0",
        description="Turn the system volume up or down, or mute it.",
        input_model=VolumeControlInput,
        output_model=VolumeControlOutput,
        risk=RiskLevel.LOW,
        required_capabilities=("device.control_volume",),
        resource_locks=(),
        timeout_seconds=5.0,
        retry_policy=RetryPolicy(max_attempts=1),
        changes_state=True,
        verification="Reports whether Windows accepted the key.",
        failure_codes=("unavailable", "rejected"),
        reversible=True,
    )

    def run(self, context: ToolContext, parameters: BaseModel) -> ToolExecution:
        assert isinstance(parameters, VolumeControlInput)
        if not media_available():
            raise ToolFailure("unavailable", "volume keys are not available here")
        if not send_media_key(parameters.action.value, repeat=parameters.steps):
            raise ToolFailure("rejected", "Windows did not accept the volume key")
        return ToolExecution(
            output=VolumeControlOutput(
                action=parameters.action.value, steps=parameters.steps, sent=True
            ),
            verification=Verification.UNVERIFIED,
            message=f"Sent {parameters.action.value} x{parameters.steps}.",
        )


# =========================================================================
# Speak
# =========================================================================
class SpeakInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = Field(min_length=1, max_length=2000)


class SpeakOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    spoken: bool
    redacted: bool
    seconds: float
    voice: str


class SpeakTool:
    """Say something aloud. Sensitive text is removed first (FR-034)."""

    spec = ToolSpec(
        tool_id="voice.speak",
        version="1.0.0",
        description="Say something aloud in the configured voice.",
        input_model=SpeakInput,
        output_model=SpeakOutput,
        risk=RiskLevel.LOW,
        required_capabilities=("voice.speak",),
        # "audio_output" was not a lock this system knows, so every attempt to
        # speak died in the invoker with a ValueError the user saw raw.
        resource_locks=("speaker_output",),
        timeout_seconds=120.0,
        retry_policy=RetryPolicy(max_attempts=1),
        changes_state=False,
        verification="Reports how much audio actually reached the output device.",
        failure_codes=("voice_unavailable", "synthesis_failed", "playback_failed"),
        redaction_keys=(),
        reversible=True,
    )

    def __init__(self, speak: Callable[[str], object]) -> None:
        self._speak = speak

    def run(self, context: ToolContext, parameters: BaseModel) -> ToolExecution:
        assert isinstance(parameters, SpeakInput)
        result = self._speak(parameters.text)
        if result is None:
            raise ToolFailure(
                "voice_unavailable",
                "no voice is available, so nothing was spoken. The Voice screen "
                "says what is missing.",
            )

        # Synthesising is not speaking. This tool reported "Spoken." on the
        # strength of having produced audio, while nothing played it — a
        # verified success for a silent room (PRD FR-048).
        playback = getattr(result, "playback", None)
        if playback is None:
            raise ToolFailure(
                "playback_failed",
                "the voice service returned audio but no playback report, so "
                "there is no evidence anything was heard.",
            )
        if not playback.played:
            raise ToolFailure(
                "playback_failed",
                f"the words were synthesised but not played: {playback.error or 'no audio reached the output device'}",
            )

        redacted = bool(getattr(result, "redacted", False))
        message = f"Spoken aloud ({playback.seconds:.1f}s)."
        if playback.interrupted:
            message = f"Started speaking, then stopped when you interrupted ({playback.seconds:.1f}s)."
        if redacted:
            message += " Sensitive content was removed first."
        return ToolExecution(
            output=SpeakOutput(
                spoken=True,
                redacted=redacted,
                seconds=round(playback.seconds, 2),
                voice=str(getattr(result, "voice_id", "")),
            ),
            # Verified means the audio really was written to the output device,
            # which is the strongest observation available here. Whether the
            # speakers were on is not something Jarvis can see.
            verification=Verification.VERIFIED,
            message=message,
        )


# =========================================================================
# Notify
# =========================================================================
class NotifyInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=600)


class NotifyOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    shown: bool
    title: str


class NotifyTool:
    """Show a desktop notification through the tray."""

    spec = ToolSpec(
        tool_id="notify.show",
        version="1.0.0",
        description="Show a notification on the desktop.",
        input_model=NotifyInput,
        output_model=NotifyOutput,
        risk=RiskLevel.LOW,
        required_capabilities=("notify.show",),
        resource_locks=(),
        timeout_seconds=10.0,
        retry_policy=RetryPolicy(max_attempts=1),
        changes_state=False,
        verification="Reports whether the notification was handed to the shell.",
        failure_codes=("no_shell",),
        reversible=True,
    )

    def __init__(self, notify: Callable[[str, str], bool]) -> None:
        self._notify = notify

    def run(self, context: ToolContext, parameters: BaseModel) -> ToolExecution:
        assert isinstance(parameters, NotifyInput)
        if not self._notify(parameters.title, parameters.message):
            raise ToolFailure(
                "no_shell",
                "there is no user interface attached, so nothing could be shown",
            )
        return ToolExecution(
            output=NotifyOutput(shown=True, title=parameters.title),
            verification=Verification.VERIFIED,
            message="Notification shown.",
        )


def register_phase1_tools(
    registry: object,
    catalogue: ApplicationCatalogue,
    *,
    speak: Callable[[str], object] | None = None,
    notify: Callable[[str, str], bool] | None = None,
) -> tuple[str, ...]:
    """Register the six approved tools. Returns what was registered.

    ``speak`` and ``notify`` need a running voice service and a shell
    respectively; without them those two tools are simply not registered, which
    is honest — an unregistered tool cannot be called at all, whereas a
    registered one that always fails looks like a defect (ADR-0010).
    """
    registered: list[str] = []
    tools: list[object] = [
        OpenApplicationTool(catalogue),
        OpenUrlTool(catalogue),
        WebSearchTool(catalogue),
        MediaControlTool(),
        VolumeControlTool(),
    ]
    if speak is not None:
        tools.append(SpeakTool(speak))
    if notify is not None:
        tools.append(NotifyTool(notify))

    for tool in tools:
        registry.register(tool)  # type: ignore[attr-defined]
        registered.append(tool.spec.tool_id)  # type: ignore[attr-defined]
    return tuple(registered)


# Re-exported so callers do not reach into ``launch`` for the enums.
__all__ += ["ArgumentKind", "LaunchKind"]
