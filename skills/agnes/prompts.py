"""Prompts da skill. Em INGLÊS — em PT o filtro do Agnes devolve HTTP 400."""

ANTES = (
    "Photorealistic before-construction version of this exact same interior. "
    "Preserve exactly the original camera position, camera height, lens perspective, "
    "room dimensions, ceiling height, wall positions, windows, doors, openings, "
    "structural columns, architectural geometry and natural lighting direction. "
    "Remove all furniture, decoration, finished flooring, wall finishes, built-in "
    "cabinets, completed lighting fixtures, luxury materials, artwork and accessories. "
    "The room is a clean unfinished construction shell: raw grey cement and plaster "
    "walls, unfinished concrete ceiling, bare concrete floor, empty space, simple "
    "natural daylight from the same direction. "
    "It must look like the exact same room before renovation began. "
    "Do not change the architecture. Do not change the camera angle. "
    "Do not add new doors or windows. No people. No furniture. No text or logos. "
    "No loose wires, no heavy construction machinery."
)

# Prompt ORIGINAL do fluxo Higgsfield/Seedance — mantido funcionando, com os
# operários em primeiro plano (o Seedance segura personagem melhor que o Agnes).
VIDEO_SEEDANCE = (
    "Create a realistic time-lapse renovation transformation video with a locked "
    "camera, before: @image1, after: @image2, showing many renovation workers "
    "actively moving around the room wearing yellow safety helmets, orange "
    "reflective safety vests, work gloves and construction boots. "
    "Show fast-paced work such as measuring walls, carrying materials, drilling, "
    "plastering, painting, installing lights, laying flooring, mounting cabinets, "
    "moving ladders, cleaning dust and assembling furniture. "
    "As the time-lapse progresses, the unfinished room gradually transforms into a "
    "fully renovated modern interior: raw cement walls become smooth finished walls, "
    "the exposed ceiling becomes a polished ceiling with lighting, bare floors become "
    "premium flooring, and the empty space fills with elegant built-ins and stylish "
    "furniture. Keep the motion busy, realistic and coordinated, with natural "
    "construction activity, dust movement and a clear sense of progress throughout."
)

# Reescrito para o Agnes (ver PLANO-AGNES.md, risco R3): o modelo é forte em
# AMBIENTE e fraco em PERSONAGEM, então a transformação do ambiente é o assunto
# e os operários ficam em segundo plano, borrados pelo movimento — que é
# exatamente o visual de um time-lapse real de obra.
VIDEO = (
    "Realistic construction time-lapse with a completely locked static camera, "
    "transforming the first keyframe into the second keyframe. "
    "The unfinished construction shell gradually becomes a fully renovated modern "
    "interior: raw cement walls become smooth finished walls, the exposed ceiling "
    "becomes a polished ceiling with working lights, the bare floor becomes premium "
    "wooden flooring, and the empty space fills with built-in cabinetry and furniture. "
    "A few construction workers in safety helmets and high-visibility vests move fast "
    "through the background, motion-blurred by the time-lapse, carrying materials and "
    "working on the walls. Floating dust in the sunlight, shifting daylight, "
    "continuous sense of progress. No camera movement, no zoom, no pan."
)
