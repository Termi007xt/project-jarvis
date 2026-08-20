"""The constrained launcher (ADR-0029).

Every test here maps to one of the nine constraints the ADR names, or to its
Enforcement section. The point is not that the launcher works — it is that the
ways it could stop being narrow are closed.
"""

from __future__ import annotations

import os

import pytest

from jarvis.toolbox.launch import (
    ALLOWED_URL_SCHEMES,
    INTERPRETER_DENYLIST,
    ApplicationCatalogue,
    ApplicationEntry,
    ArgumentKind,
    CatalogueError,
    LaunchKind,
    build_argv,
    default_catalogue,
    launch_argv,
    validate_entry,
)

WINDOWS_ONLY = pytest.mark.skipif(os.name != "nt", reason="Windows-only facility")


def executable_entry(**overrides) -> ApplicationEntry:
    defaults = dict(
        app_id="notepad",
        display_name="Notepad",
        kind=LaunchKind.EXECUTABLE,
        target=r"C:\Windows\System32\notepad.exe",
        verify_process_names=("notepad.exe",),
    )
    defaults.update(overrides)
    return ApplicationEntry(**defaults)  # type: ignore[arg-type]


# -- constraint 1: list argv only, never a string --------------------------
def test_a_command_string_is_refused() -> None:
    """A string would be re-parsed by the OS. That is the shell behaviour."""
    with pytest.raises(TypeError, match="never a command string"):
        launch_argv("notepad.exe C:/secret.txt")  # type: ignore[arg-type]


def test_an_empty_or_non_string_vector_is_refused() -> None:
    with pytest.raises(TypeError):
        launch_argv([])
    with pytest.raises(TypeError):
        launch_argv([1, 2])  # type: ignore[list-item]


# -- constraint 2: shell=False is explicit ---------------------------------
def test_the_call_site_passes_shell_false_explicitly() -> None:
    import ast
    import inspect

    from jarvis.toolbox import launch as launch_module

    tree = ast.parse(inspect.getsource(launch_module))
    popen_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "attr", None) == "Popen"
    ]
    assert len(popen_calls) == 1, "there must be exactly one Popen call"
    keywords = {kw.arg: kw.value for kw in popen_calls[0].keywords}
    assert "shell" in keywords, "shell= must be explicit, never defaulted"
    assert isinstance(keywords["shell"], ast.Constant)
    assert keywords["shell"].value is False


def test_no_env_is_constructed_at_the_call_site() -> None:
    """Constraint 7: the environment is inherited, never built from input."""
    import ast
    import inspect

    from jarvis.toolbox import launch as launch_module

    tree = ast.parse(inspect.getsource(launch_module))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "Popen":
            assert "env" not in {kw.arg for kw in node.keywords}


# -- constraint 3: the executable never comes from untrusted input ---------
def test_a_model_supplied_path_cannot_become_the_executable() -> None:
    """The model proposes which entry; it can never propose which binary."""
    catalogue = ApplicationCatalogue((executable_entry(),))
    entry = catalogue.resolve("notepad")
    assert entry is not None

    # Whatever a caller passes as the "argument", the executable stays the
    # catalogue's. The entry takes no argument at all, so this is refused.
    with pytest.raises(CatalogueError, match="does not take an argument"):
        build_argv(entry, r"C:\Windows\System32\cmd.exe")

    assert build_argv(entry)[0] == r"C:\Windows\System32\notepad.exe"


def test_resolving_by_name_never_resolves_a_path() -> None:
    catalogue = ApplicationCatalogue((executable_entry(),))
    assert catalogue.resolve(r"C:\Windows\System32\cmd.exe") is None
    assert catalogue.resolve("../../evil.exe") is None


# -- constraint 4: interpreters are refused by basename --------------------
@pytest.mark.parametrize(
    "target",
    [
        r"C:\Windows\System32\cmd.exe",
        r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
        r"C:\Program Files\PowerShell\7\pwsh.exe",
        r"C:\Windows\System32\wsl.exe",
        r"C:\Windows\System32\wscript.exe",
        r"C:\Windows\System32\mshta.exe",
        r"C:\Windows\System32\rundll32.exe",
        r"C:\Python311\python.exe",
        r"D:\somewhere\else\CMD.EXE",
    ],
)
def test_an_interpreter_cannot_be_added_to_the_catalogue(target: str) -> None:
    """Adding a shell through the catalogue is still adding a shell."""
    with pytest.raises(CatalogueError, match="interpreter or shell"):
        validate_entry(executable_entry(target=target))


def test_the_call_site_refuses_an_interpreter_even_if_something_bypasses_the_catalogue() -> None:
    with pytest.raises(CatalogueError, match="refusing to launch the interpreter"):
        launch_argv([r"C:\Windows\System32\cmd.exe", "/c", "whoami"])


def test_the_denylist_covers_the_usual_living_off_the_land_binaries() -> None:
    for name in ("cmd.exe", "powershell.exe", "wsl.exe", "mshta.exe", "regsvr32.exe"):
        assert name in INTERPRETER_DENYLIST


def test_a_non_executable_target_is_refused() -> None:
    """A document would let the file-association table choose what runs."""
    with pytest.raises(CatalogueError, match="not an executable"):
        validate_entry(executable_entry(target=r"C:\Users\me\notes.docx"))


# -- constraint 5: typed argument templates --------------------------------
@pytest.mark.parametrize(
    "url",
    [
        "file:///C:/Windows/win.ini",
        "javascript:alert(1)",
        "data:text/html,<script>",
        "steam://rungameid/12345",
        "ftp://example.com",
        "not a url at all",
    ],
)
def test_a_non_http_url_is_refused(url: str) -> None:
    entry = executable_entry(
        app_id="brave", target=r"C:\brave.exe", argument_kind=ArgumentKind.URL
    )
    with pytest.raises(CatalogueError):
        build_argv(entry, url)


def test_an_http_url_becomes_one_vector_element() -> None:
    entry = executable_entry(
        app_id="brave", target=r"C:\brave.exe", argument_kind=ArgumentKind.URL
    )
    argv = build_argv(entry, "https://www.youtube.com/watch?v=abc&t=1")
    assert argv == (r"C:\brave.exe", "https://www.youtube.com/watch?v=abc&t=1")


def test_a_url_containing_shell_metacharacters_is_still_one_element() -> None:
    """No quoting to get wrong, because nothing parses the vector."""
    entry = executable_entry(
        app_id="brave", target=r"C:\brave.exe", argument_kind=ArgumentKind.URL
    )
    nasty = 'https://example.com/?q=" & calc.exe & "'
    assert build_argv(entry, nasty)[-1] == nasty


def test_only_http_and_https_are_allowed() -> None:
    assert ALLOWED_URL_SCHEMES == {"http", "https"}


def test_a_browser_opens_with_no_url_at_all() -> None:
    """"Open Brave" is a legitimate request; it just opens the browser."""
    entry = executable_entry(
        app_id="brave", target=r"C:\brave.exe", argument_kind=ArgumentKind.URL
    )
    assert build_argv(entry) == (r"C:\brave.exe",)


def test_a_required_argument_is_still_required() -> None:
    entry = executable_entry(
        app_id="steam",
        target=r"C:\steam.exe",
        fixed_arguments=("-applaunch",),
        argument_kind=ArgumentKind.STEAM_APP_ID,
        argument_required=True,
    )
    with pytest.raises(CatalogueError, match="needs a steam_app_id"):
        build_argv(entry)


def test_a_steam_app_id_must_be_numeric() -> None:
    entry = executable_entry(
        app_id="steam",
        target=r"C:\steam.exe",
        fixed_arguments=("-applaunch",),
        argument_kind=ArgumentKind.STEAM_APP_ID,
        argument_required=True,
    )
    assert build_argv(entry, "1172620") == (r"C:\steam.exe", "-applaunch", "1172620")
    with pytest.raises(CatalogueError, match="not a Steam app id"):
        build_argv(entry, "1172620; calc.exe")


# -- constraint 6: the Store broker is fixed -------------------------------
def test_a_store_app_uses_the_fixed_explorer_broker() -> None:
    entry = ApplicationEntry(
        app_id="xbox",
        display_name="Xbox",
        kind=LaunchKind.STORE_APP,
        target="Microsoft.GamingApp_8wekyb3d8bbwe!Microsoft.Xbox.App",
    )
    argv = build_argv(entry)
    assert argv[0] == "explorer.exe", "the broker is a constant, never a catalogue value"
    assert argv[1] == "shell:AppsFolder\\Microsoft.GamingApp_8wekyb3d8bbwe!Microsoft.Xbox.App"
    assert len(argv) == 2


@pytest.mark.parametrize(
    "aumid",
    [
        "not-an-aumid",
        "Microsoft.GamingApp_8wekyb3d8bbwe",          # no bang
        'App_x!Y" & calc.exe',                        # metacharacters
        "App_x!Y\\..\\..\\evil",
        "",
    ],
)
def test_a_malformed_aumid_is_refused(aumid: str) -> None:
    with pytest.raises(CatalogueError, match="Application User Model ID"):
        validate_entry(
            ApplicationEntry(
                app_id="x", display_name="X", kind=LaunchKind.STORE_APP, target=aumid
            )
        )


# -- constraint 9: verification, and the seeded catalogue ------------------
def test_the_seed_catalogue_covers_the_prd_exit_criterion() -> None:
    """PRD section 21: Brave, YouTube, YouTube Music, Xbox, Sea of Thieves."""
    catalogue = default_catalogue()
    for app_id in ("brave", "youtube", "youtube_music", "xbox", "sea_of_thieves"):
        assert catalogue.get(app_id) is not None, f"{app_id} is missing from the seed"


def test_every_seeded_entry_declares_how_to_verify_it_started() -> None:
    """Otherwise a launch could only ever be reported as unverified."""
    for entry in default_catalogue().entries():
        assert entry.verify_process_names, f"{entry.app_id} declares no verification"


def test_every_seeded_entry_passes_validation() -> None:
    for entry in default_catalogue().entries():
        validate_entry(entry)


def test_no_seeded_path_contains_a_traversal_segment() -> None:
    """A composed path with '..' in it resolved somewhere nonsensical."""
    for entry in default_catalogue().entries():
        if entry.kind is LaunchKind.EXECUTABLE:
            assert ".." not in entry.target, f"{entry.app_id} has an unresolved path"


def test_entries_resolve_by_alias() -> None:
    catalogue = default_catalogue()
    assert catalogue.resolve("sot") is catalogue.get("sea_of_thieves")
    assert catalogue.resolve("Game Pass") is catalogue.get("xbox")


def test_an_unverified_launch_is_not_reported_as_success() -> None:
    """FR-048 and AT-018: launched is not the same as running."""
    from jarvis.toolbox.launch import LaunchOutcome

    outcome = LaunchOutcome(
        started=True, verified=False, pid=1234, argv=("x.exe",), detail="did not appear"
    )
    assert outcome.started and not outcome.verified


@WINDOWS_ONLY
def test_process_detection_finds_a_process_that_is_really_running() -> None:
    """The verification path has to actually work, or FR-064 is theatre."""
    from jarvis.toolbox.launch import process_running

    assert process_running(("python.exe",)) or process_running(("pytest.exe",))
    assert not process_running(("definitely-not-a-real-process-12345.exe",))


# =========================================================================
# "Open YouTube Music opens a tab" — and reported verified success anyway
# =========================================================================
def _music_entry() -> "ApplicationEntry":
    from jarvis.toolbox.launch import ApplicationEntry, ArgumentKind, LaunchKind

    return ApplicationEntry(
        app_id="youtube_music",
        display_name="YouTube Music",
        kind=LaunchKind.EXECUTABLE,
        target=r"C:\Program Files\Brave\chrome_proxy.exe",
        fixed_arguments=("--profile-directory=Default", "--app-id=abc123"),
        argument_kind=ArgumentKind.NONE,
        verify_process_names=("brave.exe",),
    )


def test_a_launch_is_not_verified_by_a_process_that_was_already_running(monkeypatch) -> None:
    """The defect behind "Open YouTube Music opens a tab" reporting success.

    `youtube_music` verifies against `brave.exe`. Brave is almost always already
    running, so `process_running` returned true whether or not an app window ever
    opened, and every launch recorded `succeeded / verified`. The audit log said
    the effect was confirmed while nothing about the effect had been observed.

    The rule this encodes: **a verification target must be able to distinguish
    "my effect happened" from "something unrelated was already true."**
    """
    from jarvis.toolbox import launch as launch_module

    monkeypatch.setattr(launch_module, "launch_argv", lambda argv: 4321)
    # Running before the launch, and still running after it. Which is exactly
    # what Brave looks like on a machine where the user already had it open.
    monkeypatch.setattr(launch_module, "process_running", lambda names: True)

    outcome = launch_module.launch(
        _music_entry(), verify_timeout_seconds=0.2, poll_seconds=0.01
    )

    assert outcome.started, "the launch itself still happened"
    assert not outcome.verified, (
        "brave.exe was already running before this launch, so observing it "
        "afterwards is not evidence that this launch did anything"
    )
    assert "already running" in outcome.detail.lower(), (
        "the reason has to reach the user, not just the boolean"
    )


def test_the_planner_can_see_which_applications_exist() -> None:
    """Defect 2: the model called `web.open_url` for "open YouTube Music".

    Both tools are catalogued and both look plausible, and nothing in `app.open`'s
    schema told the planner that YouTube Music *is* an application it can open.
    Handing a URL to a browser opens a tab by definition, so the launcher was
    never involved and the app-id vector was never at fault.

    The allow-list has to be visible at the moment the tool is chosen, not only
    enforced after it has been chosen wrongly.
    """
    from jarvis.toolbox.launch import default_catalogue
    from jarvis.toolbox.phase1_tools import OpenApplicationTool

    catalogue = default_catalogue()
    schema = OpenApplicationTool(catalogue).spec.json_schema_for_model()
    rendered = str(schema).casefold()

    for app_id in catalogue.ids():
        assert app_id in rendered, (
            f"'{app_id}' is approved but invisible to the planner, which is how "
            "it ends up guessing a tool instead of naming an entry"
        )


@pytest.mark.parametrize(
    "spoken",
    ["youtube-music", "youtube_music", "YouTube  Music", "  yt music  ", "YOUTUBE MUSIC"],
)
def test_an_application_resolves_however_the_model_punctuates_it(spoken: str) -> None:
    """Defect 3: `youtube-music` was refused as an unknown application.

    The model guesses separators — hyphen, underscore, space — and a catalogue
    that only matches one of them turns a correct intention into
    `unknown_application`. This is not laxity: resolution is still restricted to
    ids, display names and declared aliases, never to a path (constraint 3).
    """
    from jarvis.toolbox.launch import default_catalogue

    catalogue = default_catalogue()
    assert catalogue.resolve(spoken) is catalogue.get("youtube_music")


def test_an_unsupported_argument_says_what_can_be_done_instead() -> None:
    """Defect 3: "play Sunflower on YouTube Music" failed with only a refusal.

    ADR-0010: an honest failure names what is *not* possible and what is. Saying
    only "does not take an argument" leaves the user, and the model, with no next
    move — and invites the model to retry the same call.
    """
    from jarvis.toolbox.launch import CatalogueError, default_catalogue, launch

    entry = default_catalogue().get("youtube_music")
    assert entry is not None

    with pytest.raises(CatalogueError) as raised:
        launch(entry, "Sunflower")

    message = str(raised.value).casefold()
    assert "sunflower" in message, "say what was refused"
    assert "open" in message, "and say what it can still do"


def test_a_launch_is_verified_when_the_process_appears_because_of_it(monkeypatch) -> None:
    """The honest positive case must still work, or the fix is just pessimism."""
    from jarvis.toolbox import launch as launch_module

    observations: list[bool] = []

    def fake_process_running(names: tuple[str, ...]) -> bool:
        # Absent on the pre-launch check, present on every poll afterwards.
        observations.append(True)
        return len(observations) > 1

    monkeypatch.setattr(launch_module, "launch_argv", lambda argv: 999)
    monkeypatch.setattr(launch_module, "process_running", fake_process_running)

    outcome = launch_module.launch(
        _music_entry(), verify_timeout_seconds=2.0, poll_seconds=0.01
    )

    assert outcome.started and outcome.verified
    assert outcome.pid == 999
