import argparse
import math
from typing import Literal

import imageio
import torch
import torchvision

from haloopinate.dream import deep_dream
from haloopinate.models import PretrainedVGG16

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
VGG16 = PretrainedVGG16().to(DEVICE)


def haloopinate(
    image_path: str,
    export_path: str,
    duration: int = 10,
    fps: int = 24,
    dream_num_iterations: int = 10,
    dream_optimizer: Literal["sgd", "adam"] = "adam",
    dream_lr: float = 0.1,
    dream_pyramid_height: int = 3,
    dream_jitter: float = 0.1,
    dream_strength: float = 0.1,
    dream_coherence: float = 1.0,
    blend: float = 0.85,
    debug: bool = False,
    verbose: bool = False,
):
    image = torchvision.io.read_image(image_path).to(DEVICE)
    image = image.float() / 255.0
    assert (image.shape[-1] == image.shape[-2]) and (image.shape[-1] >= 224)

    # Deep dream
    frames = deep_dream(
        model=VGG16,
        base_image=image,
        duration=duration,
        fps=fps,
        num_iterations=dream_num_iterations,
        optimizer=dream_optimizer,
        lr=dream_lr,
        pyramid_height=dream_pyramid_height,
        jitter=dream_jitter,
        strength=dream_strength,
        coherence=dream_coherence,
        return_base=debug,
        verbose=verbose,
    )
    frames = torch.stack(frames, dim=0)  # (T C W H)

    # Hang on first frame for 1s more seamless loop
    num_freeze = math.ceil(fps / 3)
    weights = torch.linspace(start=0.0, end=1.0, steps=num_freeze).view(-1, 1, 1, 1).to(DEVICE)

    freeze = torch.stack([image] * math.ceil(fps / 3), dim=0)
    ramp_start = freeze + weights * (frames[0] - freeze)
    ramp_end = freeze + weights.flip([0]) * (frames[-1] - freeze)
    frames = torch.cat([ramp_start, frames, ramp_end, freeze], dim=0)

    # Blend video
    frames = torch.lerp(
        frames,  # current frame
        end=torch.roll(frames, shifts=1, dims=[0]),  # past frame
        weight=blend,  # mix (blend * past frame) into ((1 - blend) * current frame)
    )

    frames = frames.movedim(1, -1)  # (B C W H) -> (B W H C)
    frames = torch.round(255 * frames).clip(min=0, max=255).byte().cpu().numpy()  # [-1, 1] -> 0-255
    imageio.mimsave(export_path, frames, duration=(1000 / fps), loop=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image_path", type=str)
    parser.add_argument("--export_path", type=str)
    parser.add_argument("--duration", type=int, default=6)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--dream_num_iterations", type=int, default=10)
    parser.add_argument("--dream_optimizer", type=str, choices=["sgd", "adam"], default="adam")
    parser.add_argument("--dream_lr", type=float, default=0.1)
    parser.add_argument("--dream_pyramid_height", type=int, default=3)
    parser.add_argument("--dream_jitter", type=float, default=0.1)
    parser.add_argument("--dream_strength", type=float, default=0.1)
    parser.add_argument("--dream_coherence", type=float, default=1.0)
    parser.add_argument("--blend", type=float, default=0.85)
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("--verbose", action="store_true", default=False)
    args = parser.parse_args()

    haloopinate(**vars(args))
