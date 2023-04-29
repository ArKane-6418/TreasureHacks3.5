import math

import torch.nn as nn
import torch.optim
import torchvision.transforms as T
import torchvision.transforms.functional
import tqdm


def strength_schedule(t, base_strength):
    coherence = 2 * base_strength * (-abs(t - 0.5) + 0.5)
    return max(coherence, 0.0001)


def zoom_schedule(angle):
    angle = math.radians(angle)
    return -0.16 * angle * (angle - 2 * math.pi) + 1


def rotate_zoom_blur(image, t):
    W = image.shape[-1]
    angle = 360 * t

    zoom_scale = zoom_schedule(angle)
    image = T.functional.resize(
        image,
        size=math.ceil(image.shape[-1] * zoom_scale),
        interpolation=T.InterpolationMode.BILINEAR,
        antialias=True,
    )

    image = T.functional.rotate(
        image,
        angle=angle,
        interpolation=T.InterpolationMode.BILINEAR,
        expand=False,
    )

    image = T.functional.center_crop(image, W)

    return image, (zoom_scale, angle)


def gradient_ascent(
    model,
    image, base_image,
    act_weights,
    num_iterations, optimizer, lr,
    jitter, strength, coherence,
):
    start_image = torch.clone(image.data)

    image = nn.Parameter(image, requires_grad=True)
    OPTIMIZER_REGISTRY = {"sgd": torch.optim.SGD, "adam": torch.optim.Adam}
    optimizer = OPTIMIZER_REGISTRY[optimizer]([image], lr=lr)

    act_weights = [
        torch.where(w > 0, torch.normal(mean=w, std=jitter), 0).clip(min=0)
        for w, h in zip(act_weights, model(image))
    ]

    for _ in range(num_iterations):
        optimizer.zero_grad()

        # TODO: LPIPS?
        displacement = (image - start_image).square().mean()
        deviation = (image - base_image).square().mean()

        acts = [w * h for w, h in zip(act_weights, model(image))]
        loss = sum(-h.square().mean() for h in acts)
        loss = loss + (coherence * displacement) + (((1 / strength) - 1) * deviation)

        loss.backward()

        optimizer.step()
        image.data = image.clip(min=0, max=1)

    return torch.clone(image.data).detach()


def deep_dream(
    model,
    base_image,
    duration, fps,
    num_iterations, optimizer, lr,
    pyramid_height,
    jitter, strength, coherence,
    return_base,
    verbose,
):
    W = base_image.shape[-1]
    dream_frames = [base_image]
    pbar = tqdm.tqdm(total=(duration * fps), desc="Dreaming") if verbose else None

    num_acts = len(model(base_image))
    prev_act_weights = torch.zeros([num_acts]).to(base_image)
    next_act_weights = torch.zeros([num_acts]).to(base_image)
    next_act_weights[torch.randint(num_acts, [1]).item()] = 1.0
    prev_aug_params = (1, 0, 0.35)

    ts = torch.linspace(-1, 1, steps=(duration * fps))
    ts = 1 / (1 + torch.exp(-7 * ts))
    ts = ts - ts[0]
    ts = ts / ts[-1]

    frame = base_image
    for s in range(duration):

        for i in range(fps):
            t = ts[i + s * fps].item()
            base_frame, aug_params = rotate_zoom_blur(base_image, t=t)

            if return_base:
                dream_frames.append(base_frame)
                continue

            # We transform the current frame to match the movement of the base frame
            zoom_scale = 1.03
            rotate_angle = aug_params[1] - prev_aug_params[1]

            frame = T.functional.resize(
                frame,
                size=math.ceil(W * zoom_scale),
                interpolation=T.InterpolationMode.BILINEAR,
                antialias=True,
            )
            if frame.shape[-1] >= W:
                frame = T.functional.center_crop(frame, W)
            else:
                margin = (W - frame.shape[-1]) / 2
                frame = T.functional.pad(frame, [math.floor(margin)] * 2 + [math.ceil(margin)] * 2)
            assert frame.shape[-1] == W

            frame = T.functional.rotate(
                frame,
                angle=rotate_angle,
                interpolation=T.InterpolationMode.BILINEAR,
                expand=False,
                fill=0.0,
            )

            frame = torch.where(frame == 0.0, frame, base_frame)

            # Soft update using base frame
            frame = 0.3 * frame + 0.7 * base_frame

            # Multi-hierarchical gradient ascent
            act_weights = torch.lerp(prev_act_weights, next_act_weights, i / fps)
            for level in reversed(list(range(pyramid_height))):
                size = round(W * (1.5 ** level))
                resized_frame = T.functional.resize(frame, size=size, antialias=True)
                resized_base_frame = T.functional.resize(base_frame, size=size, antialias=True)

                frame = gradient_ascent(
                    model=model,
                    image=resized_frame,
                    base_image=resized_base_frame,
                    act_weights=act_weights,
                    num_iterations=num_iterations,
                    optimizer=optimizer,
                    lr=lr,
                    jitter=jitter,
                    strength=strength_schedule(t=t, base_strength=strength),
                    coherence=coherence,
                )

            dream_frames.append(frame)
            if verbose:
                pbar.update(1)

        prev_act_weights = next_act_weights
        next_act_weights = torch.zeros_like(prev_act_weights)
        if (s + 1) < duration:
            next_act_weights[torch.randint(num_acts, [1]).item()] = 1.0

    return dream_frames[1:]
