from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api")

PROMPT_TEMPLATES = [
    {
        "category": "E-Learning",
        "templates": [
            {"name": "Flat Illustration", "prompt": "Clean flat illustration of {subject}, professional e-learning style, simple shapes, bright colors, white background", "placeholder": "a team collaborating in a modern office"},
            {"name": "Realistic Scene", "prompt": "Photorealistic image of {subject}, professional lighting, corporate training material style", "placeholder": "a nurse checking patient vitals"},
            {"name": "Diagram Style", "prompt": "Clean educational diagram showing {subject}, labeled parts, simple colors, infographic style, white background", "placeholder": "the water cycle"},
            {"name": "Character Illustration", "prompt": "Friendly cartoon character of {subject}, diverse representation, clean lines, professional e-learning style", "placeholder": "a friendly teacher pointing at a whiteboard"},
        ],
    },
    {
        "category": "Patterns & Decorative",
        "templates": [
            {"name": "Seamless Pattern", "prompt": "Seamless tileable pattern of {subject}, repeating design, high quality, decorative", "placeholder": "geometric shapes in blue and gold"},
            {"name": "Decorative Border", "prompt": "Decorative horizontal border design with {subject}, ornamental, repeating elements, transparent background style", "placeholder": "floral vines and leaves"},
            {"name": "Background Texture", "prompt": "Subtle background texture of {subject}, soft colors, seamless, professional design", "placeholder": "watercolor wash in pastel tones"},
        ],
    },
    {
        "category": "Icons & UI",
        "templates": [
            {"name": "Icon Set", "prompt": "Professional flat icon of {subject}, consistent style, simple shapes, clean design, solid background", "placeholder": "a graduation cap"},
            {"name": "UI Illustration", "prompt": "Modern UI illustration of {subject}, minimal style, soft gradients, tech startup aesthetic", "placeholder": "cloud computing concept"},
        ],
    },
    {
        "category": "Scenarios",
        "templates": [
            {"name": "Workplace Scene", "prompt": "Professional photograph of {subject}, diverse team, modern workplace, well-lit, corporate style", "placeholder": "employees in a safety training session"},
            {"name": "Medical/Health", "prompt": "Professional medical illustration of {subject}, clean, accurate, educational style", "placeholder": "proper hand washing technique"},
            {"name": "Technology", "prompt": "Modern technology scene showing {subject}, clean aesthetic, professional photography style", "placeholder": "someone using a tablet for learning"},
        ],
    },
]

QUALITY_ENHANCERS = {
    "general": ", highly detailed, professional quality, 4k, sharp focus",
    "illustration": ", vector art style, clean lines, vibrant colors, professional illustration",
    "photo": ", DSLR photography, 85mm lens, natural lighting, bokeh background, high resolution",
    "artistic": ", masterful composition, award-winning, trending on artstation, beautiful lighting",
}


@router.get("/templates")
def get_templates():
    return PROMPT_TEMPLATES


class EnhanceRequest(BaseModel):
    prompt: str
    style: str = "general"


@router.post("/enhance-prompt")
def enhance_prompt(req: EnhanceRequest):
    suffix = QUALITY_ENHANCERS.get(req.style, QUALITY_ENHANCERS["general"])
    enhanced = req.prompt.rstrip(", .") + suffix
    return {"original": req.prompt, "enhanced": enhanced, "style": req.style}
