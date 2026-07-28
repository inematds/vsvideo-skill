# Create a Virtual Staging Renovation Video With One Codex Skill

Virtual staging videos are a powerful way to show how an unfinished room can become a completed interior. Instead of manually creating every image, writing prompts, and moving files between different tools, we can control the full workflow with one Codex skill.

In this tutorial, we start from a blank project, attach one interior-design image directly inside the Codex chat, generate a matching before-construction image, and turn the two images into a realistic renovation time-lapse using Higgsfield Seedance 2.0 Mini.

The complete process is managed by one `SKILL.md` file.

## Start From a Blank Project

The project begins with an empty folder. Inside it, we create an output folder and a folder for the virtual staging skill.

```text
virtual-staging-video/
│
├── output/
│
└── skills/
    └── virtual-staging-video/
        └── SKILL.md
```

The `SKILL.md` file contains everything Codex needs to complete the project. This includes the workflow instructions, GPT Image prompt, image consistency rules, video prompt, model routing, fallback logic, and output locations.

There is no need for separate image-analysis, prompt-library, or video-director skills. This is a small and predictable workflow, so one orchestration skill is enough.

## What the Skill Does

The skill begins by analysing the interior-design image attached to the Codex chat.

It identifies the camera position, room dimensions, perspective, walls, windows, doors, ceiling, furniture, materials, lighting, and interior style.

The submitted interior image is treated as the completed after-renovation reference.

Codex then uses GPT Image 2 to generate a matching before-construction version of the same room. The most important requirement is visual consistency.

The generated image must preserve the same:

- Camera angle
- Room dimensions
- Windows and doors
- Wall positions
- Ceiling height
- Perspective
- Structural features

Only the construction stage should change.

The finished furniture, flooring, wall materials, built-in cabinets, decoration, lighting fixtures, and luxury finishes are removed. The room becomes a clean unfinished construction shell with raw walls, bare flooring, an unfinished ceiling, and simple natural lighting.

## GPT Image 2 Fallback Mechanism

Codex GPT Image 2 remains the primary image-generation method.

The skill first attempts to generate the before-construction image directly through Codex. If the function returns an error, times out, or does not create a usable image, Codex retries the request once.

If the second attempt also fails, the workflow automatically switches to the GPT Image 2 option available through Higgsfield.

The same reference image and the same prompt are used, so the intended result does not change.

The routing order is:

```text
Codex GPT Image 2
        ↓
Retry Codex GPT Image 2
        ↓
Higgsfield GPT Image 2 Fallback
        ↓
Validate Generated Image
```

This fallback prevents a temporary image-generation issue from stopping the entire project.

Before running the demo, connect the Higgsfield plugin by following the connection guide on the website. After completing the connection, open the ChatGPT app and confirm that Higgsfield is available.

## Create the Renovation Video

Once the before-construction image is ready, the skill prepares the two references:

```text
@image1 = Before Construction
@image2 = Completed Interior
```

Both images are then sent to Higgsfield Seedance 2.0 Mini.

The video prompt asks the model to create a realistic renovation time-lapse with a locked camera. Renovation workers move around the room wearing safety helmets, reflective vests, gloves, and construction boots.

They perform actions such as measuring walls, carrying materials, drilling, plastering, painting, installing lights, laying flooring, mounting cabinets, moving ladders, assembling furniture, and cleaning dust.

As the time-lapse progresses, the unfinished room gradually becomes the completed interior.

Raw walls become smooth finished walls. The exposed ceiling becomes a polished ceiling with installed lighting. Bare floors become premium flooring, and the empty space fills with built-ins, furniture, and decoration.

The workers make the transformation feel more believable and help hide small differences between the before and after images.

The camera must remain locked throughout the video so the room geometry stays stable.

## Run Everything Inside Codex

For the final demo, attach the completed interior-design image directly inside the Codex chat.

Then use one instruction:

```text
Use the attached interior-design image to create a virtual
staging renovation video.

Follow the virtual-staging-video skill.

Use Codex GPT Image 2 as the primary image generator.
If it fails after one retry, use the Higgsfield GPT Image 2
route as the fallback.

Generate the renovation video with Higgsfield Seedance 2.0 Mini
and save all generated files inside the project.
```

Codex reads the skill, analyses the attached image, generates the before-construction version, validates the image pair, prepares the Seedance prompt, generates the renovation video, and saves the results.

The final project contains:

```text
output/
├── before-construction.png
├── completed-interior.png
├── renovation-video.mp4
└── generation-log.json
```

The result is a complete virtual staging renovation video created from one attached interior image, one Codex instruction, and one skills file.

This workflow is useful for real estate marketing, off-plan property promotion, renovation previews, interior-design presentations, and social-media property content.

## Resources

Virtual Staging Skill
