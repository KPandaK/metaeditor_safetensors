MODELSPEC_FIELDS = [
	"title", "description", "author", "date", "license", "usage hint", "thumbnail", "tags", "merged from"
]

MODELSPEC_TOOLTIPS = {
	"title": "A human-readable name for the model.",
	"description": "A user-friendly description of the model and its purpose.",
	"author": "The name or identity of the company or person that created the model.",
	"date": "Date and time the model was created or published (Local Time).",
	"license": "License under which the model is released.",
	"usage hint": "Hints for using the model, where applicable.",
	"thumbnail": "A small thumbnail icon, recommended (256x256 JPEG)",
	"tags": "Comma-separated tags describing the model.",
	"merged from": "Comma-separated list of source models (if applicable)."
}

MODELSPEC_KEY_MAP = {
	"title": "modelspec.title",
	"description": "modelspec.description",
	"author": "modelspec.author",
	"date": "modelspec.date",
	"license": "modelspec.license",
	"usage hint": "modelspec.usage_hint",
	"thumbnail": "modelspec.thumbnail",
	"tags": "modelspec.tags",
	"merged from": "modelspec.merged_from"
}

# File Size Limits
LARGE_FILE_WARNING_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
THUMBNAIL_SIZE_WARNING = 2 * 1024 * 1024  # 2MB
THUMBNAIL_TARGET_SIZE = 256  # pixels
THUMBNAIL_QUALITY = 85

# Input Validation
MAX_FIELD_LENGTH = 1000  # Maximum length for text fields
MAX_DESCRIPTION_LENGTH = 5000  # Longer limit for description
REQUIRED_FIELDS = []  # Fields that must have values (empty = none required)

GITHUB_URL = "https://github.com/KPandaK/metaeditor_safetensors"