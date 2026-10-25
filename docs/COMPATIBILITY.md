# Inventor compatibility policy

Documentation reviewed: **2026-10-25**. API availability is evidence of a possible port, not proof that every operation works on every release, Windows build or locale.

| Inventor | Internal major | Status in 0.2.0 |
|---|---:|---|
| 2017–2021 | 21–25 | API candidate; enabled, not live-tested |
| 2022 | 26 | Live-tested reference release |
| 2023–2024 | 27–28 | API candidate; enabled, not live-tested |
| 2025–2027 | 29–31 | API candidate; enabled, not live-tested |
| Before 2017 | Below 21 | Rejected: pattern-definition baseline not met |
| After 2027 | Above 31 | Rejected by default; explicit experimental opt-in only |

## Why the range was expanded

Autodesk documents Inventor's Automation API and external-process access, including Python. The bridge uses **Python COM out of process**, rather than loading a managed DLL into Inventor. [Autodesk API overview](https://forge.autodesk.com/developer/overview/inventor-api) and [getting started](https://help.autodesk.com/view/INVNTOR/2025/ENU/?guid=GUID-4939ABD1-A15E-473E-9376-D8208EC029EB).

The connector now reads `IDispatch.GetTypeInfo().GetContainingTypeLib()` from the running application, generates pywin32 wrappers for that actual type library, binds the returned interface and uses its constants. It no longer hardcodes one type-library version or requires major 26. `SoftwareVersion` supplies the release identity; the documented year/major relationship is used for 2017 and later. [SoftwareVersion](https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-API/files/SoftwareVersion.htm).

The minimum is driven by the APIs already used by this engine:

| API | Autodesk documents introduction | Source |
|---|---|---|
| ExtrudeFeatures.CreateExtrudeDefinition | 2012 | [Reference](https://help.autodesk.com/cloudhelp/2026/ENU/Inventor-API/files/ExtrudeFeatures_CreateExtrudeDefinition.htm) |
| RectangularPatternFeatures.CreateDefinition | 2017 | [Reference](https://help.autodesk.com/cloudhelp/2023/ENU/Inventor-API/files/RectangularPatternFeatures_CreateDefinition.htm) |
| CircularPatternFeatures.CreateDefinition | 2017 | [Reference](https://help.autodesk.com/cloudhelp/2025/ENU/Inventor-API/files/CircularPatternFeatures_CreateDefinition.htm) |
| MirrorFeatures.CreateDefinition | 2017 | [Reference](https://help.autodesk.com/cloudhelp/2024/ENU/Inventor-API/files/MirrorFeatures_CreateDefinition.htm) |
| Face.Appearance | 2014 | [Reference](https://help.autodesk.com/cloudhelp/2026/ENU/Inventor-API/files/Face_Appearance.htm) |
| NonParametricBaseFeatures.AddByDefinition | 2011 | [Reference](https://help.autodesk.com/cloudhelp/2023/ENU/Inventor-API/files/NonParametricBaseFeatures_AddByDefinition.htm) |

Autodesk's 2027 documentation still exposes the pattern definitions and part-component interfaces used here: [CircularPatternFeatureDefinition](https://help.autodesk.com/cloudhelp/2027/ENU/Inventor-API/files/CircularPatternFeatureDefinition.htm), [PartComponentDefinition](https://help.autodesk.com/cloudhelp/2027/ENU/Inventor-API/files/PartComponentDefinition.htm). These checks justify a candidate range through 2027, not a blanket guarantee of full API compatibility.

Requested feature methods are checked on the actual COM objects before starting the edit transaction. Missing members produce an explicit compatibility error. Geometry updates, feature health, volume changes and requested bounds are checked at runtime. Optional model-history compaction reports a warning if unavailable; it does not discard geometry. These probes cannot replace the live test suite.

## .NET changes in newer Inventor releases

Autodesk documents its move to .NET 8 for managed add-ins beginning with Inventor 2025. This bridge does not load a .NET add-in and does not reference Autodesk managed interop assemblies; therefore it does not require rebuilding a managed add-in for that transition. This is an architectural inference, **not a live-test claim for 2025+**. Inventor itself still requires Autodesk's supported runtime and updates. [Creating an Add-In](https://help.autodesk.com/cloudhelp/2026/ENU/Inventor-API/files/CreatingAnAddIn_Overview.htm).

## File formats are a separate compatibility issue

An IPT/IAM is saved in the format of the attached Inventor release. The plugin cannot save an older native format. Opening newer files in older Inventor has Autodesk's interoperability restrictions; use STEP when feature-history loss is acceptable. [Autodesk: opening newer files](https://help.autodesk.com/cloudhelp/2024/ENU/Inventor-Help/files/GUID-489A3E1D-EB3E-4468-9592-F2EAD0E584DD.htm).

## Selecting a version and adding test evidence

Launch the desired Inventor manually, with only that instance running. Use `install.ps1 -InventorYear 2024` to require the matching release; this is a guard, not a version launcher. The COM Running Object Table is not a reliable multi-instance selector. Run the [live suites](TESTING.md), review the reports for private paths and submit a compatibility issue. Only reproducible passing evidence should move a release from `api_candidate` to `tested`.

For an unrevised future release, developers may set `AI_CAD_ALLOW_FUTURE=1` in the server environment for explicit experimentation. The response remains `experimental`. Do not change the reviewed range solely because the version number increments.
