# Virtual Staging Video Skill

## Objective

Create a realistic virtual staging renovation video from one
submitted interior-design image.

Use GPT Image to create the matching before-construction image.

Use the submitted interior-design image as the completed after image.

Use Higgsfield Seedance 2.0 Mini (Higgsfield MCP) to create a realistic renovation
time-lapse between the before and after images.

## Project Files

Input:

- input/interior-design.png

Outputs:

- output/before-construction.png
- output/completed-interior.png
- output/renovation-video.mp4

## Workflow

1. Find the interior-design image inside the input folder.

2. Analyse the image and identify:

   - room type
   - camera position
   - perspective
   - room dimensions
   - walls
   - windows
   - doors and openings
   - ceiling height
   - flooring
   - furniture
   - built-in features
   - materials
   - lighting direction
   - interior-design style

3. Use the submitted image as the completed after reference.

4. Generate a matching before-construction image with GPT Image.

5. Preserve the exact architecture and camera perspective.

6. Save the generated image as:

   output/before-construction.png

7. Save or copy the submitted image as:

   output/completed-interior.png

8. Use the before image as @image1.

9. Use the completed interior as @image2.

10. Generate the renovation video with Higgsfield Seedance 2.0 Mini. Using Higgsfield MCP

11. Save the completed video as:

   output/renovation-video.mp4

## Before-Construction Image Prompt

Create a photorealistic before-construction version of the submitted
completed interior.

Preserve exactly:

- the original camera position
- camera height
- lens perspective
- room dimensions
- ceiling height
- wall positions
- windows
- doors
- openings
- structural columns
- architectural geometry
- natural lighting direction

Remove:

- all furniture
- decoration
- finished flooring
- wall finishes
- built-in cabinets
- completed lighting fixtures
- luxury materials
- artwork
- accessories

Transform the room into a clean unfinished construction shell with
raw cement or plaster walls, an unfinished ceiling, bare flooring,
empty space, and simple natural daylight.

The output must look like the exact same room before renovation began.

Do not change the architecture.
Do not change the camera angle.
Do not add new doors or windows.
Do not add people.
Do not add furniture.
Do not add text or logos.
Avoid exposed loose wires and complicated construction machinery.

## Consistency Rules

The before and after images must show the same room from the same
camera position.

Lock:

- camera angle
- perspective
- room dimensions
- ceiling height
- walls
- windows
- doors
- openings
- structural features

Only the construction stage and interior finishes should change.

Do not continue to video generation if the before image has a
different room layout or camera angle.

## Seedance Video Prompt

Create a realistic time-lapse renovation transformation video with
a locked camera, before: @image1, after: @image2 showing many
renovation workers actively moving around the room wearing yellow
safety helmets, orange reflective safety vests, work gloves, and
construction boots.

Show fast-paced work such as measuring walls, carrying materials,
drilling, plastering, painting, installing lights, laying flooring,
mounting cabinets, moving ladders, cleaning dust, and assembling
furniture.

As the time-lapse progresses, the unfinished room gradually
transforms into a fully renovated modern interior, with raw cement
walls becoming smooth finished walls, the exposed ceiling becoming
a polished ceiling with lighting, bare floors becoming premium
flooring, and the empty space filling with elegant built-ins and
stylish furniture.

Keep the motion busy, realistic, and coordinated, with natural
construction activity, dust movement, and a clear sense of progress
throughout.
