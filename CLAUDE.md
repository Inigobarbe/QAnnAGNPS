# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

QAnnAGNPS is a QGIS 3 plugin (Python, PyQt5/`qgis.PyQt`) that wraps the AnnAGNPS model (ANNualized
AGricultural NonPoint Source, a soil-erosion / diffuse-pollution simulator) so it can be configured, run,
and post-processed from inside QGIS: building the TopAGNPS/AnnAGNPS control and input files, launching
the external model executables, visualizing outputs, and running sensitivity analysis and calibration on
top of it.

This directory **is** the live QGIS plugin install (`.../QGIS3/profiles/default/python/plugins/qannagnps`),
not a separate source checkout — there is no build/deploy step to get edits into QGIS. QGIS picks up
`.py` changes on plugin reload (e.g. the "Plugin Reloader" plugin, or restarting QGIS); `.ui` changes are
read live by `uic.loadUiType` at runtime, no compilation needed.

## Commands

There is no system Python on this machine and no working automated test/build pipeline. For any
verification, use QGIS's own bundled interpreter, e.g.:

```
"C:\Program Files\QGIS <version>\apps\Python3XX\python.exe" -m py_compile qannagnps.py
```

That only checks syntax. Anything beyond that (importing `qgis.core`, rendering matplotlib figures,
running an actual AnnAGNPS/TopAGNPS simulation) requires the full QGIS process/environment and generally
can't be driven headlessly from a shell here — verify by reloading the plugin inside a running QGIS
instance and exercising the relevant dialog against a real project.

`Makefile`, `pb_tool.cfg`, and `scripts/*.sh` are unmodified Plugin Builder boilerplate left over from
this plugin's original scaffold (they still reference a plugin named `ephemeral_gully` and Unix tooling
like `nosetests`/`lrelease`). They do not reflect this plugin's actual file list and are not used for
day-to-day development — don't rely on `make test`/`make deploy`/etc.

`test/` is the same generic Plugin Builder scaffold. `test/test_ephemeral_gully_dialog.py` imports
`from ephemeral_gully_dialog import EphemeralGullyDialog`, a module that doesn't exist anywhere in this
repo, so it fails on collection. The rest of the suite (`test_init.py`, `test_qgis_environment.py`,
`test_resources.py`, `test_translations.py`) is the stock scaffold and needs a real QGIS test environment
(`get_qgis_app()` in `test/utilities.py`) to run at all. Treat this suite as unmaintained, not as a
verification tool for changes.

## Architecture

**Single monolithic controller.** Almost all logic lives in one class, `qannagnps` in `qannagnps.py`
(~10k lines, ~290 methods), instantiated by `classFactory()` in `__init__.py`. `initGui()` constructs
*every* dialog up front and wires essentially all Qt signal/slot connections in one place, rather than
each dialog owning its own logic.

**Dialog wrapper pattern.** Each `ui/*.ui` (Qt Designer file) has a thin Python wrapper in `ui/*.py`
(typically ~20-44 lines) that only does `uic.loadUiType(...)` + `setupUi(self)`. No behavior lives there.
All reading/writing of widget state happens in `qannagnps.py`, addressed by the widget's Designer
`objectName` (e.g. `self.dlg_calibration.runoff`, `self.dlg_calibration.combo_metric`). The `objectName`s
in a `.ui` file are therefore a contract with `qannagnps.py`: renaming or removing one breaks the wiring
silently (an `AttributeError` at runtime, not a load-time failure), so when editing a `.ui`, keep every
`objectName` that `qannagnps.py` references, or update both sides together.

**Project folder convention.** The user selects one working directory; the plugin creates
`<workdir>/<project name>/{Preprocessing_inputs,Preprocessing_outputs,Processing_inputs,Processing_outputs}`.
When parallelizing (sensitivity analysis, calibration), this structure is mirrored per `Core_N` subfolder,
one per available CPU core.

**External model execution.** AnnAGNPS/TopAGNPS are external Windows executables bundled under
`Executables/`, launched via `subprocess` (also via numbered `.bat` wrappers, e.g.
`EjecutarAnnAGNPS_1.bat`..`_11.bat`, one per parallel core). A module-level `threading.Lock`
(`qgis_processing_lock`) serializes calls into the QGIS `processing` plugin, which isn't safe to call
concurrently from multiple `QgsTask` workers.

**Parallel analyses as `QgsTask`s.** `Sensitivity_Parallelization` and `Calibration_Parallelization`
(bottom of `qannagnps.py`) are `QgsTask` subclasses that each run one AnnAGNPS execution in its own
`Core_N` folder. `qannagnps.py` dispatches/collects them via `lanzar_siguiente_sensitivity` /
`lanzar_siguiente_calibration` → `finalizar_tarea_sensitivity` / `finalizar_tarea_calibration`, connected
to each task's `taskCompleted`/`taskTerminated` signals. Calibration runs a round-based ask/tell loop
against a Bayesian optimizer (`skopt.Optimizer`, vendored in `libraries/skopt`); sensitivity analysis uses
Sobol/Morris sampling (vendored in `libraries/SALib`). Both vendored libraries are imported with relative
imports (`from .libraries.SALib...`, `from .libraries.skopt...`) — they are not pip dependencies and won't
be found in site-packages.

**Calibration output/metric selection.** Which AnnAGNPS output the calibration compares against observed
data is chosen via radio buttons (`self.dlg_calibration.runoff/total_erosion/nitrogen/organic/phosphorus`)
and resolved in `calibration_output_data_type()`, which feeds `self.import_df(data_type, core,
sensitivity=True)` — the same output-parsing helper the sensitivity-analysis path (`save_result`) uses, so
adding/adjusting a calibratable output should go through `import_df` rather than parsing AnnAGNPS output
CSVs again. The objective metric (NSE/RMSE/PBIAS/KGE) is computed generically in
`compute_calibration_metric`/`metric_is_better`, not hardcoded to one metric.

**Icon addressing (two conventions coexist).** Some icons are referenced through the compiled Qt resource
file (`resources.py`/`resources.qrc`, paths like `:/plugins/qannagnps/images/logo.svg`), used for the
toolbar actions. Others are referenced directly from disk (`os.path.join(plugin_directory, "images",
...)`), used for icons set at runtime in `initGui()` / `setup_calibration_ui_enhancements()`. Match
whichever convention the surrounding code already uses rather than mixing them in one spot.

**Language mix.** Code comments and many internal variable/method names are Spanish (e.g.
`asignar_valores_control_dialogo`, `crear_carpeta`), while user-facing UI strings are English. Follow the
existing convention in whatever file you're editing rather than translating existing code.

**Other directories.** `Documentation/` holds official AnnAGNPS/TopAGNPS component PDF manuals (AGBUF,
AGFLOW, TopAGNPS, etc.) — the authoritative reference for control-file fields. `ArchivosDialogos/` is
leftover C++/Qt Widgets source from an earlier prototype and is not used by the Python plugin.
`sample_observed_data/` holds synthetic (invented) example CSVs, not real measurements, only for
previewing the observed-data graph in the calibration dialog.
