"""Cliente mínimo da API Agnes AI (imagens + vídeo keyframes).

Fatos de API medidos em ~/projetos/agnes-nei/NOTAS-API.md:
- img2img ignora `ratio` -> usar `size` explícito em pixels.
- máx. 10 MB por imagem de referência.
- ~34% de HTTP 503 na geração -> retry com backoff.
- vídeo: rate limit REAL de 5 req/min -> throttle.
- vídeo é assíncrono: POST /v1/videos -> GET /agnesapi?video_id=...
- keyframes aceitam data URI base64 (não precisa de URL pública).
- o JSON do vídeo MENTE sobre o tamanho: conferir com ffprobe.
"""

import base64
import json
import os
import time
import urllib.error
import urllib.request

BASE = "https://apihub.agnes-ai.com"
ENV_PATH = os.path.expanduser("~/projetos/agnes-nei/.env")

IMAGE_MODEL = "agnes-image-2.1-flash"
VIDEO_MODEL = "agnes-video-v2.0"


def api_key() -> str:
    """Lê a chave em runtime do .env do agnes-nei. Nunca copiar nem imprimir."""
    key = os.environ.get("AGNES_API_KEY")
    if key:
        return key.strip()
    with open(ENV_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("AGNES_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError(f"AGNES_API_KEY não encontrada em {ENV_PATH}")


def _post(path: str, payload: dict, timeout: int = 600) -> dict:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _get(path: str, timeout: int = 120) -> dict:
    req = urllib.request.Request(
        BASE + path, headers={"Authorization": f"Bearer {api_key()}"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _with_retry(fn, tentativas: int = 5, base_espera: float = 6.0):
    """Retry com backoff. Sempre mostra o erro CRU da API — no NOTAS-API a
    mensagem crua sempre estava certa e a conclusão automática, errada."""
    ultimo = None
    for i in range(tentativas):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            corpo = e.read().decode(errors="replace")[:400]
            ultimo = f"HTTP {e.code}: {corpo}"
            print(f"  [api] {ultimo}")
            if e.code in (400, 401, 403):  # determinístico, não adianta repetir
                raise RuntimeError(ultimo) from e
            espera = base_espera * (i + 1)
            if e.code == 429:
                espera = max(espera, 65)  # 5 req/min no vídeo
            print(f"  [api] retry em {espera:.0f}s ({i + 1}/{tentativas})")
            time.sleep(espera)
        except (urllib.error.URLError, TimeoutError) as e:
            ultimo = f"rede: {e}"
            print(f"  [api] {ultimo} — retry em {base_espera * (i + 1):.0f}s")
            time.sleep(base_espera * (i + 1))
    raise RuntimeError(f"falhou após {tentativas} tentativas — {ultimo}")


def data_uri(caminho: str) -> str:
    with open(caminho, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    return "data:image/png;base64," + b64


def gerar_imagem(prompt: str, size: str = "1312x736", refs=None) -> bytes:
    """text2img (refs=None) ou img2img (refs = lista de data URIs / URLs).

    `size` em pixels explícitos e SEM `ratio` — no img2img o `ratio` é ignorado
    e a imagem volta 1024x1024.
    """
    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "size": size,
        "extra_body": {"response_format": "b64_json"},
    }
    if refs:
        payload["extra_body"]["image"] = list(refs)

    resp = _with_retry(lambda: _post("/v1/images/generations", payload))
    item = resp["data"][0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    with urllib.request.urlopen(item["url"], timeout=300) as r:
        return r.read()


def gerar_video(prompt, keyframes, num_frames=145, frame_rate=24,
                width=1312, height=736, seed=None, poll=8, teto=900) -> bytes:
    """Vídeo por keyframes A->B. num_frames deve seguir 8n+1 e ser <= 441."""
    if num_frames > 441:
        raise ValueError("num_frames <= 441 (18,4s @24fps)")
    if (num_frames - 1) % 8 != 0:
        raise ValueError("num_frames deve seguir a regra 8n+1")

    payload = {
        "model": VIDEO_MODEL,
        "prompt": prompt,
        "num_frames": num_frames,
        "frame_rate": frame_rate,
        "width": width,
        "height": height,
        "extra_body": {"image": list(keyframes), "mode": "keyframes"},
    }
    if seed is not None:
        payload["extra_body"]["seed"] = seed

    resp = _with_retry(lambda: _post("/v1/videos", payload))
    vid = resp.get("id") or resp.get("video_id") or resp.get("data", {}).get("id")
    if not vid:
        raise RuntimeError(f"resposta sem id de vídeo: {json.dumps(resp)[:400]}")
    print(f"  [video] job {vid} — aguardando")

    inicio = time.time()
    while time.time() - inicio < teto:
        time.sleep(poll)
        st = _with_retry(lambda: _get(f"/agnesapi?video_id={vid}"), tentativas=3)
        status = st.get("status") or st.get("data", {}).get("status")
        print(f"  [video] {int(time.time() - inicio)}s status={status}")
        if status == "completed":
            url = (st.get("url") or st.get("video_url")
                   or st.get("data", {}).get("url")
                   or (st.get("output") or [None])[0])
            if not url:
                raise RuntimeError(f"completed sem url: {json.dumps(st)[:400]}")
            with urllib.request.urlopen(url, timeout=600) as r:
                return r.read()
        if status == "failed":
            raise RuntimeError(f"geração falhou: {json.dumps(st)[:400]}")
    raise RuntimeError(f"timeout de {teto}s aguardando o vídeo {vid}")
