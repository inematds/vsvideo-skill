"""Pipeline Agnes consistente em três estágios para vídeos de cerca de 18 s."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path


WIDTH = 1312
HEIGHT = 736
FRAMES_PER_SEGMENT = 145
FPS = 24
MAX_STAGE_ATTEMPTS = 3

ARCHITECTURE_LOCK = (
    "The FIRST reference image is the immutable architecture and camera anchor. "
    "Keep exactly its camera position, crop, camera height, lens perspective, room "
    "dimensions, ceiling height, wall edges, windows, doors, openings, columns and "
    "lighting direction. Never invent, remove, resize or move architectural elements. "
    "The SECOND reference, when supplied, is the immediately later construction stage "
    "and must guide temporal continuity without overriding the first reference. "
    "Return the identical 16:9 composition. No people, silhouettes, body parts, text "
    "or logos. "
)

# A geração ocorre de trás para frente: final -> 3 -> 2 -> 1.
STAGE_PROMPTS = {
    3: (
        ARCHITECTURE_LOCK
        + "Create the late-finishing stage immediately before this completed room. "
        "Keep all final built-in cabinetry locations and lighting positions fixed, "
        "but show them partially installed. Flooring, walls and ceiling are finished. "
        "Remove loose furniture, artwork, plants, accessories and final styling."
    ),
    2: (
        ARCHITECTURE_LOCK
        + "Create the rough-finishing stage immediately before the later stage. Show "
        "wall preparation, partial plaster and primer, floor substrate, protected "
        "openings, fixed electrical points and only the structural frames of built-in "
        "cabinetry that exist in the final anchor. No finished flooring, loose "
        "furniture, decor or completed lighting."
    ),
    1: (
        ARCHITECTURE_LOCK
        + "Create the earliest clean construction stage immediately before the rough "
        "stage. Show the same empty architectural shell with unfinished wall surfaces, "
        "bare floor substrate and unfinished ceiling. Preserve every opening and "
        "structural edge. Remove furniture, cabinetry, decor and finished fixtures."
    ),
}

VIDEO_PROMPTS = (
    (
        "Locked-off construction time-lapse from the exact raw-shell keyframe to the "
        "exact rough-finishing keyframe. Only wall preparation, floor substrate and "
        "fixed utility details progress. Exactly two construction workers are visible: "
        "one prepares a wall surface and one works on the open floor area. They use "
        "small realistic hand tools and materials remain attached to their real "
        "surfaces."
    ),
    (
        "Locked-off construction time-lapse from the exact rough-finishing keyframe "
        "to the exact late-finishing keyframe. Plaster, paint, flooring, fixed "
        "lighting and built-in cabinetry assemble gradually in their final locations. "
        "Exactly two construction workers are visible: one paints or installs a fixed "
        "wall finish and one installs flooring or cabinetry from the open room area. "
        "They use only small realistic tools."
    ),
    (
        "Locked-off interior completion time-lapse from the exact late-finishing "
        "keyframe to the exact completed-room keyframe. Only final cabinetry details, "
        "furniture, curtains, lighting, accessories and cleaning appear progressively "
        "in their final locations. Exactly two construction workers are visible while "
        "placing normal-sized furniture and completing cleaning. Before the final "
        "keyframe, both leave through an existing visible doorway so the final room is "
        "empty."
    ),
)

PHYSICS_LOCK = (
    " The first and last keyframes are mandatory visual anchors. The camera is a fixed "
    "tripod: zero pan, tilt, zoom, roll, reframing or lens change. Preserve walls, "
    "openings, window divisions, ceiling, floor boundaries and perspective throughout. "
    "Show exactly two adult construction workers, never more. Keep each worker's full "
    "body anatomically stable, with both feet on the visible floor. Workers stay in "
    "open walkable areas, remain separate from each other and use only visible doors "
    "or openings to enter or leave. No worker or object may pass through a wall, "
    "window, floor, ceiling, cabinet, furniture or another solid object. No clones, "
    "partial bodies, extra limbs, flying materials, teleportation, melting, warping, "
    "duplicated objects or impossible physics. Use restrained time-lapse motion and "
    "subtle clean dissolves only."
)

# Edge-map SSIM is deliberately stricter near the final image, where geometry and
# built-ins should already be almost identical.
MIN_PAIR_SIMILARITY = {3: 0.50, 2: 0.47, 1: 0.44}


class ConsistencyError(RuntimeError):
    """Os keyframes não são seguros para gerar vídeo."""

    def __init__(self, message: str, *, similarity: float | None = None) -> None:
        super().__init__(message)
        self.similarity = similarity


def _load_agnes(skill_dir: Path):
    sys.path.insert(0, str(skill_dir))
    import client  # type: ignore[import-not-found]

    return client


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{encoded}"


def _run(command: list[str], *, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _normalize_image(source: Path, destination: Path) -> Path:
    """Normaliza uma imagem para a composição única usada pelo pipeline."""

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg não encontrado")
    _run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-vf",
            (
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},setsar=1"
            ),
            "-frames:v",
            "1",
            str(destination),
        ]
    )
    _require_dimensions(destination)
    print(f"[normalize] {WIDTH}x{HEIGHT} -> {destination}")
    return destination


def _normalize_reference(reference: Path, output: Path) -> Path:
    """Cria uma única composição 16:9 usada por imagens e vídeos."""

    return _normalize_image(
        reference,
        output / "stage-4-final-reference.png",
    )


def _dimensions(path: Path) -> tuple[int, int]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe não encontrado")
    result = _run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0",
            str(path),
        ],
        timeout=30,
    )
    try:
        width, height = result.stdout.strip().split(",", 1)
        return int(width), int(height)
    except (TypeError, ValueError) as exc:
        raise ConsistencyError("não foi possível validar as dimensões") from exc


def _require_dimensions(path: Path) -> None:
    if _dimensions(path) != (WIDTH, HEIGHT):
        raise ConsistencyError(
            f"{path.name} não possui a composição obrigatória {WIDTH}x{HEIGHT}"
        )


def _edge_similarity(first: Path, second: Path) -> float:
    """Compara mapas de bordas para detectar deriva de câmera/arquitetura."""

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg não encontrado")
    result = subprocess.run(
        [
            ffmpeg,
            "-v",
            "info",
            "-i",
            str(first),
            "-i",
            str(second),
            "-lavfi",
            (
                "[0:v]scale=656:368,format=gray,"
                "edgedetect=low=0.05:high=0.15[e0];"
                "[1:v]scale=656:368,format=gray,"
                "edgedetect=low=0.05:high=0.15[e1];"
                "[e0][e1]ssim"
            ),
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise ConsistencyError("não foi possível comparar os estágios")
    matches = re.findall(r"All:([0-9.]+)", result.stderr)
    if not matches:
        raise ConsistencyError("a comparação dos estágios não retornou resultado")
    return float(matches[-1])


def _validate_pair(
    stage: int,
    earlier: Path,
    later: Path,
    *,
    allow_warning: bool = False,
) -> float:
    _require_dimensions(earlier)
    _require_dimensions(later)
    similarity = _edge_similarity(earlier, later)
    minimum = MIN_PAIR_SIMILARITY[stage]
    print(
        f"[consistency stage-{stage}] edge_ssim={similarity:.4f} "
        f"minimum={minimum:.2f}"
    )
    if similarity < minimum:
        if allow_warning:
            print(
                f"[consistency stage-{stage}] aviso aceito após as tentativas"
            )
            return similarity
        raise ConsistencyError(
            f"stage-{stage} alterou demais a câmera ou a arquitetura",
            similarity=similarity,
        )
    return similarity


def _generate_stages(
    client,
    reference: Path,
    output: Path,
    *,
    validator: Callable[[int, Path, Path], float] = _validate_pair,
) -> tuple[list[Path], dict[str, float]]:
    """Gera 3 -> 2 -> 1, sempre mantendo a referência final como primeira âncora."""

    generated: dict[int, Path] = {}
    metrics: dict[str, float] = {}
    reference_uri = _data_uri(reference)
    later = reference
    for stage in (3, 2, 1):
        path = output / f"stage-{stage}.png"
        last_error: ConsistencyError | None = None
        best_image: bytes | None = None
        best_similarity = -1.0
        for attempt in range(1, MAX_STAGE_ATTEMPTS + 1):
            refs = [reference_uri]
            if later != reference:
                refs.append(_data_uri(later))
            image = client.gerar_imagem(
                STAGE_PROMPTS[stage],
                size=f"{WIDTH}x{HEIGHT}",
                refs=refs,
            )
            path.write_bytes(image)
            try:
                metrics[f"stage-{stage}-to-{stage + 1}"] = validator(
                    stage, path, later
                )
            except ConsistencyError as exc:
                last_error = exc
                if (
                    exc.similarity is not None
                    and exc.similarity > best_similarity
                ):
                    best_similarity = exc.similarity
                    best_image = image
                print(
                    f"[stage {stage}] rejeitado na tentativa "
                    f"{attempt}/{MAX_STAGE_ATTEMPTS}: {exc}"
                )
                if attempt == MAX_STAGE_ATTEMPTS:
                    if best_image is not None:
                        path.write_bytes(best_image)
                    metrics[f"stage-{stage}-to-{stage + 1}"] = max(
                        best_similarity, 0.0
                    )
                    print(
                        f"[stage {stage}] melhor tentativa aceita com aviso "
                        f"após {MAX_STAGE_ATTEMPTS} tentativas"
                    )
                    generated[stage] = path
                    later = path
                    break
                continue
            print(f"[stage {stage}] aprovado na tentativa {attempt} -> {path}")
            generated[stage] = path
            later = path
            break
        if stage not in generated:
            raise ConsistencyError(
                f"stage-{stage} não pôde ser gerado: {last_error}"
            )
    return [
        generated[1],
        generated[2],
        generated[3],
        reference,
    ], metrics


def _validate_stages(stages: list[Path]) -> dict[str, float]:
    if len(stages) != 4:
        raise ConsistencyError("são necessários quatro keyframes")
    metrics: dict[str, float] = {}
    for path in stages:
        _require_dimensions(path)
    for index in range(3):
        stage = index + 1
        metrics[f"stage-{stage}-to-{stage + 1}"] = _validate_pair(
            stage,
            stages[index],
            stages[index + 1],
            allow_warning=True,
        )
    return metrics


def _write_report(output: Path, metrics: dict[str, float]) -> Path:
    warnings = [
        name
        for name, similarity in metrics.items()
        if similarity < MIN_PAIR_SIMILARITY[int(name.split("-")[1])]
    ]
    report = output / "consistency-report.json"
    report.write_text(
        json.dumps(
            {
                "status": (
                    "approved_with_warnings" if warnings else "approved"
                ),
                "dimensions": f"{WIDTH}x{HEIGHT}",
                "edgeSimilarity": metrics,
                "peopleAllowed": False,
                "warnings": warnings,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    if warnings:
        (output / "consistency-warning.txt").write_text(
            "Uma ou mais etapas foram aceitas com aviso após três tentativas.",
            encoding="utf-8",
        )
    return report


def _create_contact_sheet(stages: list[Path], output: Path) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg não encontrado")
    contact = output / "approval-contact-sheet.jpg"
    command = [ffmpeg, "-y"]
    for stage in stages:
        command.extend(["-i", str(stage)])
    labels = ("1 RAW SHELL", "2 ROUGH FINISH", "3 LATE FINISH", "4 FINAL")
    filters = []
    names = []
    for index, label in enumerate(labels):
        name = f"s{index}"
        names.append(f"[{name}]")
        filters.append(
            f"[{index}:v]scale=640:352,"
            f"drawtext=text='{label}':x=18:y=18:fontsize=25:"
            f"fontcolor=white:box=1:boxcolor=black@0.65[{name}]"
        )
    filters.append(
        "".join(names) + "xstack=inputs=4:layout=0_0|640_0|0_352|640_352[out]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[out]",
            "-frames:v",
            "1",
            str(contact),
        ]
    )
    _run(command)
    return contact


def _generate_segments(client, stages: list[Path], output: Path) -> list[Path]:
    segments: list[Path] = []
    for index in range(3):
        path = output / f"segment-{index + 1}.mp4"
        video = client.gerar_video(
            VIDEO_PROMPTS[index] + PHYSICS_LOCK,
            keyframes=[_data_uri(stages[index]), _data_uri(stages[index + 1])],
            num_frames=FRAMES_PER_SEGMENT,
            frame_rate=FPS,
            width=WIDTH,
            height=HEIGHT,
            seed=70428 + index,
        )
        path.write_bytes(video)
        segments.append(path)
        print(f"[segment {index + 1}/3] ok -> {path}")
    return segments


def _concatenate(segments: list[Path], output: Path) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg não encontrado")
    final = output / "renovation-video-18s.mp4"
    command = [ffmpeg, "-y"]
    for segment in segments:
        command.extend(["-i", str(segment)])
    command.extend(
        [
            "-filter_complex",
            "[0:v:0][1:v:0][2:v:0]concat=n=3:v=1:a=0[v]",
            "-map",
            "[v]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(final),
        ]
    )
    _run(command)
    print(f"[concat] ok -> {final}")
    return final


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--mode", required=True, choices=("preview", "auto18", "render18")
    )
    parser.add_argument("--image")
    parser.add_argument("--stages", nargs=4)
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    client = _load_agnes(skill_dir)

    try:
        if args.mode in {"preview", "auto18"}:
            if not args.image:
                raise SystemExit("--image é obrigatório")
            reference = _normalize_reference(Path(args.image).resolve(), output)
            stages, metrics = _generate_stages(client, reference, output)
        else:
            if not args.stages:
                raise SystemExit("--stages é obrigatório")
            stages = [Path(value).resolve() for value in args.stages]
            if any(not path.is_file() for path in stages):
                raise SystemExit("estágio aprovado não encontrado")
            metrics = _validate_stages(stages)
        _write_report(output, metrics)

        if args.mode == "preview":
            _create_contact_sheet(stages, output)
            return 0
        segments = _generate_segments(client, stages, output)
        _concatenate(segments, output)
        return 0
    except ConsistencyError as exc:
        (output / "consistency-error.txt").write_text(str(exc), encoding="utf-8")
        print(f"[consistency] rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
