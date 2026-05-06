#!/usr/bin/env python3
"""
Kie.ai Product Visualizer - Nano Banana Pro / 2

Generyczny edytor zdjec produktowych (balustrady, porecze, klamki, ogrodzenia
i inne produkty z branzy najdek.pl). Bierze zdjecie referencyjne + krotki opis
zmiany i zwraca wizualizacje.

Tryby:
    edit    - 1 zdjecie + prompt
    compose - 2+ zdjec (pierwsze = scena, kolejne = referencje stylu) + prompt
    batch   - wiele promptow na tym samym zdjeciu/zdjeciach

Usage:
    python3 kie_balustrade.py edit --prompt "zmniejsz liczbe poprzecznych rurek z 4 do 3" \\
        --image input.jpg --output out.jpg

    python3 kie_balustrade.py compose --prompt "zamontuj te porecz na tej scianie" \\
        --image scena.jpg --image porecz-ref.jpg --output out.jpg

    python3 kie_balustrade.py batch --prompt "kolor czarny" --prompt "kolor bialy" \\
        --image input.jpg --output-dir output/
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import boto3
import requests
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ENV_FILE = SKILL_DIR / ".env"
GLOBAL_ENV_FILE = Path.home() / ".claude" / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
elif GLOBAL_ENV_FILE.exists():
    load_dotenv(GLOBAL_ENV_FILE)
else:
    load_dotenv()

KIE_API_KEY = os.environ.get("KIE_API_KEY")
BASE_URL = "https://api.kie.ai/api/v1"

S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
S3_PUBLIC_URL = os.environ.get("S3_PUBLIC_URL")

ASPECT_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "auto"]
RESOLUTIONS = ["1K", "2K", "4K"]
FORMATS = ["jpg", "png"]
MODELS = ["nano-banana-pro", "nano-banana-2"]


def check_s3_config():
    missing = []
    if not S3_ENDPOINT_URL:
        missing.append("S3_ENDPOINT_URL")
    if not S3_ACCESS_KEY:
        missing.append("S3_ACCESS_KEY")
    if not S3_SECRET_KEY:
        missing.append("S3_SECRET_KEY")
    if not S3_BUCKET:
        missing.append("S3_BUCKET")
    if missing:
        raise Exception(
            f"Brak konfiguracji S3 w .env: {', '.join(missing)}.\n"
            f"Sprawdz plik {ENV_FILE} (skopiuj z .env.example)"
        )


def upload_to_s3(local_path: str) -> str:
    check_s3_config()

    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION,
    )

    filename = os.path.basename(local_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    key = f"kie-balustrades/{timestamp}_{unique_id}_{filename}"

    ext = Path(local_path).suffix.lower().lstrip(".")
    content_type = f"image/{'jpeg' if ext == 'jpg' else ext}"

    print(f"  Upload do S3: {filename}...")
    s3.upload_file(
        local_path,
        S3_BUCKET,
        key,
        ExtraArgs={"ContentType": content_type},
    )

    base = S3_PUBLIC_URL or S3_ENDPOINT_URL
    url = f"{base.rstrip('/')}/{S3_BUCKET}/{key}"
    print(f"  URL: {url}")
    return url


def build_edit_prompt(user_prompt: str) -> str:
    return f"{user_prompt.strip()} Keep the rest of the photo unchanged."


def build_compose_prompt(user_prompt: str) -> str:
    return (
        f"Use the first image as the scene. "
        f"Use the additional images as visual references. "
        f"{user_prompt.strip()} "
        f"Keep the first image's scene unchanged."
    )


def create_task(prompt: str, image_urls: list, ratio: str, resolution: str,
                output_format: str, model: str, seed: int = None) -> str:
    input_data = {
        "prompt": prompt,
        "image_input": image_urls,
        "aspect_ratio": ratio,
        "google_search": False,
        "resolution": resolution,
        "output_format": output_format,
    }
    if seed is not None:
        input_data["seed"] = seed

    payload = {
        "model": model,
        "input": input_data,
    }

    response = requests.post(
        f"{BASE_URL}/jobs/createTask",
        headers={"Authorization": f"Bearer {KIE_API_KEY}"},
        json=payload,
        timeout=30,
    )

    if response.status_code == 401:
        raise Exception("401 Unauthorized - sprawdz KIE_API_KEY w pliku .env")
    if response.status_code == 402:
        raise Exception("402 Payment Required - brak srodkow na koncie Kie.ai (https://kie.ai)")
    if response.status_code == 422:
        raise Exception(f"422 Validation Error: {response.text}")
    if response.status_code == 429:
        raise Exception("429 Rate Limit - poczekaj 30s i sprobuj ponownie")
    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    data = response.json()
    if "data" not in data or "taskId" not in data["data"]:
        raise Exception(f"Unexpected response: {data}")

    return data["data"]["taskId"]


def poll_task(task_id: str, max_attempts: int = 60) -> dict:
    for attempt in range(max_attempts):
        time.sleep(5)

        response = requests.get(
            f"{BASE_URL}/jobs/recordInfo",
            headers={"Authorization": f"Bearer {KIE_API_KEY}"},
            params={"taskId": task_id},
            timeout=30,
        )

        if response.status_code != 200:
            raise Exception(f"Poll error {response.status_code}: {response.text}")

        data = response.json()["data"]
        state = data.get("state", "unknown")

        if state == "success":
            return json.loads(data.get("resultJson", "{}"))
        if state == "fail":
            raise Exception(f"Generation failed: {data.get('failMsg', 'Unknown error')}")

        print(f"  [{attempt + 1}/{max_attempts}] Generating... (status: {state})")

    raise Exception(f"Timeout after {max_attempts * 5}s")


def download_image(url: str, output_path: str):
    response = requests.get(url, timeout=60)
    if response.status_code != 200:
        raise Exception(f"Download error {response.status_code}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)


def run_generation(prompt: str, image_urls: list, output: str, ratio: str,
                   resolution: str, fmt: str, model: str, label: str = "",
                   seed: int = None):
    if label:
        print(f"\n=== {label} ===")
    print(f"  Output: {output}")
    print(f"  Model: {model} | Ratio: {ratio} | Resolution: {resolution} | Format: {fmt}")
    print(f"  Reference images: {len(image_urls)}")
    print(f"  Prompt: {prompt}")
    if seed is not None:
        print(f"  Seed: {seed}")

    task_id = create_task(prompt, image_urls, ratio, resolution, fmt, model, seed)
    print(f"  Task ID: {task_id}")

    result = poll_task(task_id)

    if "resultUrls" not in result or not result["resultUrls"]:
        raise Exception(f"Brak wyniku w odpowiedzi: {result}")

    download_image(result["resultUrls"][0], output)
    print(f"  Zapisano: {output}")


def cmd_edit(args):
    if not os.path.exists(args.image):
        raise Exception(f"Nie znaleziono pliku: {args.image}")

    image_url = upload_to_s3(args.image)
    prompt = build_edit_prompt(args.prompt)

    run_generation(
        prompt=prompt,
        image_urls=[image_url],
        output=args.output,
        ratio=args.ratio,
        resolution=args.resolution,
        fmt=args.format,
        model=args.model,
        label="Edit",
        seed=args.seed,
    )


def cmd_compose(args):
    image_urls = []
    for img_path in args.images:
        if not os.path.exists(img_path):
            raise Exception(f"Nie znaleziono pliku: {img_path}")
        image_urls.append(upload_to_s3(img_path))

    prompt = build_compose_prompt(args.prompt)

    run_generation(
        prompt=prompt,
        image_urls=image_urls,
        output=args.output,
        ratio=args.ratio,
        resolution=args.resolution,
        fmt=args.format,
        model=args.model,
        label=f"Compose ({len(image_urls)} ref images)",
        seed=args.seed,
    )


def cmd_batch(args):
    prompts = list(args.prompts) if args.prompts else []
    if args.prompts_file:
        with open(args.prompts_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    prompts.append(line)

    if not prompts:
        raise Exception("Batch wymaga --prompt (mozna wielokrotnie) lub --prompts-file")

    image_paths = args.images or []
    if not image_paths:
        raise Exception("Batch wymaga --image (1 = edit, 2+ = compose)")

    for img_path in image_paths:
        if not os.path.exists(img_path):
            raise Exception(f"Nie znaleziono pliku: {img_path}")

    print(f"\nUpload {len(image_paths)} zdjec do S3 (raz, ponowne uzycie dla wszystkich wariantow)...")
    image_urls = [upload_to_s3(p) for p in image_paths]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    is_compose = len(image_urls) > 1
    failed = []

    print(f"\nBatch: {len(prompts)} promptow")
    print(f"Output dir: {output_dir.resolve()}\n")

    for idx, user_prompt in enumerate(prompts, start=1):
        output_file = output_dir / f"variant_{idx:02d}_{timestamp}.{args.format}"
        print(f"\n[{idx}/{len(prompts)}]")
        try:
            prompt = (build_compose_prompt(user_prompt)
                      if is_compose else build_edit_prompt(user_prompt))
            run_generation(
                prompt=prompt,
                image_urls=image_urls,
                output=str(output_file),
                ratio=args.ratio,
                resolution=args.resolution,
                fmt=args.format,
                model=args.model,
                label=f"Variant {idx}: {user_prompt[:60]}",
                seed=args.seed,
            )
        except Exception as e:
            print(f"  BLAD: {e}")
            failed.append((idx, user_prompt, str(e)))

    print(f"\n=== Gotowe ===")
    print(f"Sukces: {len(prompts) - len(failed)}/{len(prompts)}")
    if failed:
        print(f"Bledy:")
        for idx, prompt, err in failed:
            print(f"  - [{idx}] {prompt[:60]}: {err}")


def main():
    parser = argparse.ArgumentParser(description="Kie.ai Product Visualizer (Nano Banana Pro / 2)")
    sub = parser.add_subparsers(dest="mode", required=True)

    common_args = [
        ("--model", {"default": "nano-banana-pro", "choices": MODELS, "help": "Model AI (default: nano-banana-pro - lepsza jakosc, drozszy)"}),
        ("--ratio", {"default": "auto", "choices": ASPECT_RATIOS, "help": "Proporcje (default: auto)"}),
        ("--resolution", {"default": "2K", "choices": RESOLUTIONS, "help": "Rozdzielczosc (default: 2K)"}),
        ("--format", {"default": "jpg", "choices": FORMATS, "help": "Format pliku (default: jpg)"}),
        ("--seed", {"type": int, "default": None, "help": "Seed dla powtarzalnosci. Brak = losowy."}),
    ]

    edit = sub.add_parser("edit", help="1 zdjecie + prompt")
    edit.add_argument("--prompt", required=True, help="Krotki opis zmiany (po polsku lub angielsku)")
    edit.add_argument("--image", required=True, help="Sciezka do zdjecia referencyjnego")
    edit.add_argument("--output", required=True, help="Sciezka pliku wyjsciowego")
    for name, kwargs in common_args:
        edit.add_argument(name, **kwargs)

    compose = sub.add_parser("compose", help="2+ zdjec (1. = scena, kolejne = referencje)")
    compose.add_argument("--prompt", required=True, help="Krotki opis tego co chcemy zrobic")
    compose.add_argument("--image", action="append", dest="images", required=True,
                         help="Zdjecia (uzyj wielokrotnie: --image scena.jpg --image ref.jpg)")
    compose.add_argument("--output", required=True)
    for name, kwargs in common_args:
        compose.add_argument(name, **kwargs)

    batch = sub.add_parser("batch", help="Wiele promptow na tym samym zdjeciu/zdjeciach")
    batch.add_argument("--prompt", action="append", dest="prompts", default=[],
                       help="Prompt (mozna podac wielokrotnie)")
    batch.add_argument("--prompts-file", help="Plik tekstowy: 1 prompt per linia")
    batch.add_argument("--image", action="append", dest="images", required=True,
                       help="Zdjecia (1 = edit, 2+ = compose)")
    batch.add_argument("--output-dir", required=True)
    for name, kwargs in common_args:
        batch.add_argument(name, **kwargs)

    args = parser.parse_args()

    if not KIE_API_KEY:
        print("Error: KIE_API_KEY nie jest ustawiony.")
        print(f"Utworz plik .env w: {SKILL_DIR}")
        print("Skopiuj .env.example do .env i wstaw swoj klucz z https://kie.ai")
        sys.exit(1)

    if args.mode == "edit":
        cmd_edit(args)
    elif args.mode == "compose":
        cmd_compose(args)
    elif args.mode == "batch":
        cmd_batch(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
