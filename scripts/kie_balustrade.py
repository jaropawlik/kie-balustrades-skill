#!/usr/bin/env python3
"""
Kie.ai Balustrade Generator - Nano Banana 2

Skrypt do generowania wizualizacji balustrad balkonowych z referencyjnych zdjec.
Czyta KIE_API_KEY i S3 credentials z pliku .env w katalogu skilla.

Tryby:
    edit    - 1 zdjecie referencyjne + instrukcja -> wizualizacja balustrady
    compose - 2+ zdjec referencyjnych (np. budynek + balustrada) -> kompozycja
    batch   - wiele wariantow (slupkow x rurek) z tym samym zdjeciem

Usage:
    # Edit z 1 zdjecia
    python3 kie_balustrade.py edit --posts 6 --rails 4 \\
        --image input.jpg --output out.jpg

    # Compose z 2+ zdjec
    python3 kie_balustrade.py compose --posts 6 --rails 4 \\
        --image building.jpg --image railing-ref.jpg --output out.jpg

    # Batch - wiele wariantow z tego samego zdjecia
    python3 kie_balustrade.py batch --posts 5,6,7 --rails 3,4,5 \\
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

NUMBER_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
    6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
    11: "eleven", 12: "twelve",
}

COLOR_DESCRIPTIONS = {
    "antracyt": "anthracite powder-coated steel, matte finish (RAL 7016)",
    "czarny": "jet black painted steel, satin finish",
    "bialy": "pure white powder-coated steel, matte finish (RAL 9016)",
    "srebrny": "brushed stainless steel, satin metallic finish",
    "rdzawy": "corten steel with weathered rust patina, warm orange-brown",
}


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


def number_to_words(n: int) -> str:
    return NUMBER_WORDS.get(n, str(n))


def get_color_description(color: str) -> str:
    if color.startswith("#") and len(color) == 7:
        return f"custom color {color} painted steel, matte finish"
    return COLOR_DESCRIPTIONS.get(color, COLOR_DESCRIPTIONS["antracyt"])


def build_edit_instruction(posts: int, rails: int, color: str,
                           extra: str = None) -> str:
    posts_word = number_to_words(posts)
    rails_word = number_to_words(rails)
    color_desc = get_color_description(color)

    instruction = (
        f"PRESERVE FROM REFERENCE IMAGE:\n"
        f"Keep the entire building EXACTLY as shown in the reference - facade, "
        f"walls, windows, window frames, balcony slab, roof, surrounding "
        f"environment, lighting conditions, time of day, perspective and "
        f"camera angle. Do not modify any architectural elements other than "
        f"the railing.\n\n"
        f"CHANGE - REPLACE ONLY THE BALCONY RAILING:\n"
        f"Remove the existing balcony railing and replace it with a new modern "
        f"steel railing.\n\n"
        f"NEW RAILING SPECIFICATIONS:\n"
        f"- The railing MUST have EXACTLY {posts} ({posts_word}) vertical posts, "
        f"evenly spaced from left to right.\n"
        f"- The railing MUST have EXACTLY {rails} ({rails_word}) horizontal "
        f"cross-rails, parallel to each other, equal spacing between them.\n"
        f"- Color and material: {color_desc}.\n"
        f"- Style: modern minimalist, slim rectangular profile, complete and "
        f"unbroken structure, every post connected to every horizontal rail.\n"
        f"- Mounting: posts visibly mounted to the balcony floor or balcony "
        f"front edge with clean metal connections.\n\n"
        f"COUNT VERIFICATION: The final image MUST contain {posts} vertical "
        f"posts (not {posts - 1}, not {posts + 1}) and {rails} horizontal "
        f"rails (not {rails - 1}, not {rails + 1}).\n\n"
        f"DO NOT:\n"
        f"- Do not alter the building walls, windows, facade or any "
        f"architectural details.\n"
        f"- Do not change lighting, shadows, time of day or weather.\n"
        f"- Do not add any decorative elements not specified above.\n"
        f"- Do not add text, watermarks, logos or signatures."
    )

    if extra:
        instruction += f"\n\nADDITIONAL NOTES:\n{extra}"

    return instruction


def build_compose_instruction(posts: int, rails: int, color: str,
                              extra: str = None) -> str:
    posts_word = number_to_words(posts)
    rails_word = number_to_words(rails)
    color_desc = get_color_description(color)

    instruction = (
        f"REFERENCE IMAGES:\n"
        f"The first image is the main scene (building with balcony). "
        f"Additional images are style/material references for the railing.\n\n"
        f"PRESERVE FROM FIRST IMAGE:\n"
        f"Keep the entire building EXACTLY as shown in the first image - facade, "
        f"walls, windows, balcony slab, roof, lighting and perspective. Do not "
        f"modify any architectural elements other than the railing.\n\n"
        f"CHANGE - INSTALL NEW BALCONY RAILING:\n"
        f"Place a new modern steel railing on the balcony of the first image, "
        f"styled according to the additional reference images.\n\n"
        f"NEW RAILING SPECIFICATIONS:\n"
        f"- The railing MUST have EXACTLY {posts} ({posts_word}) vertical posts, "
        f"evenly spaced.\n"
        f"- The railing MUST have EXACTLY {rails} ({rails_word}) horizontal "
        f"cross-rails, parallel, equal spacing.\n"
        f"- Color and material: {color_desc}.\n"
        f"- Style: modern minimalist, slim rectangular profile, complete and "
        f"unbroken structure, every post connected to every rail.\n\n"
        f"COUNT VERIFICATION: The final image MUST contain {posts} vertical "
        f"posts and {rails} horizontal rails.\n\n"
        f"Match the lighting, perspective and architectural style of the first "
        f"(main) image.\n\n"
        f"DO NOT:\n"
        f"- Do not alter the building, walls, windows or any architectural "
        f"details from the first image.\n"
        f"- Do not change lighting or perspective.\n"
        f"- Do not add text, watermarks, logos or signatures."
    )

    if extra:
        instruction += f"\n\nADDITIONAL NOTES:\n{extra}"

    return instruction


def create_task(prompt: str, image_urls: list, ratio: str, resolution: str,
                output_format: str, seed: int = None) -> str:
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
        "model": "nano-banana-2",
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
                   resolution: str, fmt: str, label: str = "",
                   seed: int = None):
    print(f"\n=== {label} ===" if label else "")
    print(f"  Output: {output}")
    print(f"  Ratio: {ratio} | Resolution: {resolution} | Format: {fmt}")
    print(f"  Reference images: {len(image_urls)}")
    if seed is not None:
        print(f"  Seed: {seed}")

    task_id = create_task(prompt, image_urls, ratio, resolution, fmt, seed)
    print(f"  Task ID: {task_id}")

    result = poll_task(task_id)

    if "resultUrls" not in result or not result["resultUrls"]:
        raise Exception(f"Brak wyniku w odpowiedzi: {result}")

    download_image(result["resultUrls"][0], output)
    print(f"  Zapisano: {output}")


def parse_int_list(value: str) -> list:
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def cmd_edit(args):
    if not os.path.exists(args.image):
        raise Exception(f"Nie znaleziono pliku: {args.image}")

    image_url = upload_to_s3(args.image)
    instruction = build_edit_instruction(
        args.posts, args.rails, args.color, args.extra,
    )

    run_generation(
        prompt=instruction,
        image_urls=[image_url],
        output=args.output,
        ratio=args.ratio,
        resolution=args.resolution,
        fmt=args.format,
        label=f"Edit: {args.posts}x{args.rails} ({args.color})",
        seed=args.seed,
    )


def cmd_compose(args):
    image_urls = []
    for img_path in args.images:
        if not os.path.exists(img_path):
            raise Exception(f"Nie znaleziono pliku: {img_path}")
        image_urls.append(upload_to_s3(img_path))

    instruction = build_compose_instruction(
        args.posts, args.rails, args.color, args.extra,
    )

    run_generation(
        prompt=instruction,
        image_urls=image_urls,
        output=args.output,
        ratio=args.ratio,
        resolution=args.resolution,
        fmt=args.format,
        label=f"Compose: {args.posts}x{args.rails} ({args.color}, {len(image_urls)} ref images)",
        seed=args.seed,
    )


def cmd_batch(args):
    posts_list = parse_int_list(args.posts)
    rails_list = parse_int_list(args.rails)

    if not posts_list or not rails_list:
        raise Exception("--posts i --rails musza zawierac co najmniej jedna wartosc")

    image_paths = args.images if args.images else ([args.image] if args.image else [])
    if not image_paths:
        raise Exception("Batch wymaga --image (1 zdjecie) lub --image kilka razy (compose)")

    for img_path in image_paths:
        if not os.path.exists(img_path):
            raise Exception(f"Nie znaleziono pliku: {img_path}")

    print(f"\nUpload {len(image_paths)} zdjec do S3 (raz, ponowne uzycie dla wszystkich wariantow)...")
    image_urls = [upload_to_s3(p) for p in image_paths]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    total = len(posts_list) * len(rails_list)
    done = 0
    failed = []

    print(f"\nBatch: {total} wariantow ({len(posts_list)} slupkow x {len(rails_list)} rurek)")
    print(f"Output dir: {output_dir.resolve()}\n")

    is_compose = len(image_urls) > 1

    for posts in posts_list:
        for rails in rails_list:
            done += 1
            output_file = output_dir / f"balustrada_{posts}x{rails}_{args.color}_{timestamp}.{args.format}"
            print(f"\n[{done}/{total}]")
            try:
                if is_compose:
                    instruction = build_compose_instruction(posts, rails, args.color, args.extra)
                else:
                    instruction = build_edit_instruction(posts, rails, args.color, args.extra)

                run_generation(
                    prompt=instruction,
                    image_urls=image_urls,
                    output=str(output_file),
                    ratio=args.ratio,
                    resolution=args.resolution,
                    fmt=args.format,
                    label=f"{posts}x{rails} ({args.color})",
                    seed=args.seed,
                )
            except Exception as e:
                print(f"  BLAD: {e}")
                failed.append((posts, rails, str(e)))

    print(f"\n=== Gotowe ===")
    print(f"Sukces: {total - len(failed)}/{total}")
    if failed:
        print(f"Bledy:")
        for posts, rails, err in failed:
            print(f"  - {posts}x{rails}: {err}")


def main():
    parser = argparse.ArgumentParser(description="Kie.ai Balustrade Generator")
    sub = parser.add_subparsers(dest="mode", required=True)

    common_args = [
        ("--color", {"default": "antracyt", "help": "Kolor (antracyt/czarny/bialy/srebrny/rdzawy lub #XXXXXX)"}),
        ("--extra", {"default": None, "help": "Dodatkowe instrukcje dla AI"}),
        ("--ratio", {"default": "auto", "choices": ASPECT_RATIOS, "help": "Proporcje (default: auto - dopasowane do zdjecia)"}),
        ("--resolution", {"default": "2K", "choices": RESOLUTIONS, "help": "Rozdzielczosc (default: 2K)"}),
        ("--format", {"default": "jpg", "choices": FORMATS, "help": "Format pliku (default: jpg)"}),
        ("--seed", {"type": int, "default": None, "help": "Seed dla powtarzalnosci (np. 42). Brak = losowy."}),
    ]

    edit = sub.add_parser("edit", help="1 zdjecie + balustrada wg parametrow")
    edit.add_argument("--posts", type=int, required=True, help="Liczba slupkow")
    edit.add_argument("--rails", type=int, required=True, help="Liczba rurek poprzecznych")
    edit.add_argument("--image", required=True, help="Sciezka do zdjecia referencyjnego")
    edit.add_argument("--output", required=True, help="Sciezka pliku wyjsciowego")
    for name, kwargs in common_args:
        edit.add_argument(name, **kwargs)

    compose = sub.add_parser("compose", help="2+ zdjec (np. budynek + referencja balustrady)")
    compose.add_argument("--posts", type=int, required=True)
    compose.add_argument("--rails", type=int, required=True)
    compose.add_argument("--image", action="append", dest="images", required=True,
                         help="Zdjecia (uzyj wielokrotnie: --image a.jpg --image b.jpg)")
    compose.add_argument("--output", required=True)
    for name, kwargs in common_args:
        compose.add_argument(name, **kwargs)

    batch = sub.add_parser("batch", help="Wiele wariantow z tego samego zdjecia/zdjec")
    batch.add_argument("--posts", required=True, help="Lista slupkow (np. 5,6,7)")
    batch.add_argument("--rails", required=True, help="Lista rurek (np. 3,4,5)")
    batch.add_argument("--image", action="append", dest="images",
                       help="Zdjecia (1 = edit, 2+ = compose, mozna uzyc wielokrotnie)")
    batch.add_argument("--output-dir", required=True, help="Katalog wyjsciowy")
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
        if not hasattr(args, 'image'):
            args.image = None
        cmd_batch(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
