# Reply Classification API

## Overview

This module provides sentiment classification for text responses, specifically designed for analyzing stakeholder replies in WOO (Wet open overheid / Open Government Act) requests. It uses zero-shot classification to determine whether a response indicates agreement or objection to publication.

## Model

- **Model**: `cross-encoder/nli-deberta-v3-small`
- **Type**: Zero-shot classification using Natural Language Inference
- **Languages**: Primarily Dutch, but supports multilingual text
- **Classification Labels**:
  - "agrees to publish"
  - "objects to publication"

## API Endpoints

### POST `/classification/classify`

Classify text to determine sentiment regarding publication.

**Request Body:**
```json
{
  "text": "Bedankt voor jullie bericht. Ik heb graag liever niet dat jullie dit publiceren."
}
```

**Response:**
```json
{
  "text": "Bedankt voor jullie bericht. Ik heb graag liever niet dat jullie dit publiceren.",
  "classification": "objects to publication",
  "confidence": 0.89,
  "all_scores": {
    "objects to publication": 0.89,
    "agrees to publish": 0.11
  }
}
```

**Status Codes:**
- `200 OK`: Classification successful
- `400 Bad Request`: Empty or invalid text
- `500 Internal Server Error`: Model initialization or classification failed

### GET `/classification/health`

Check if the classification service is ready.

**Response:**
```json
{
  "status": "ready",
  "model": "cross-encoder/nli-deberta-v3-small",
  "candidate_labels": ["agrees to publish", "objects to publication"]
}
```

## Usage Examples

### Using cURL

```bash
# Classify text
curl -X POST "http://localhost:8000/classification/classify" \
  -H "Content-Type: application/json" \
  -d '{"text": "Ja, jullie mogen dit gerust publiceren."}'

# Check health
curl "http://localhost:8000/classification/health"
```

### Using Python

```python
import requests

# Classify text
response = requests.post(
    "http://localhost:8000/classification/classify",
    json={"text": "Ik heb bezwaar tegen publicatie van deze informatie."}
)
result = response.json()
print(f"Classification: {result['classification']}")
print(f"Confidence: {result['confidence']:.2%}")
```

### Using JavaScript/TypeScript

```typescript
// Classify text
const response = await fetch('http://localhost:8000/classification/classify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Dit is prima, jullie mogen dit publiceren.'
  })
});

const result = await response.json();
console.log(`Classification: ${result.classification}`);
console.log(`Confidence: ${(result.confidence * 100).toFixed(1)}%`);
```

## Model Performance

The model uses zero-shot classification, meaning it can classify text without specific training on this task. Key characteristics:

- **Accuracy**: Good performance on clear agreement/objection statements
- **Confidence Scores**: Typically high (>0.7) for unambiguous statements
- **Ambiguous Cases**: May produce lower confidence scores (<0.6) for neutral or unclear statements
- **Language**: Optimized for Dutch text but supports multilingual input

## Implementation Details

### Lazy Loading

The classification model is loaded on first use rather than at application startup. This:
- Reduces initial startup time
- Saves memory when the endpoint isn't used
- Allows the main application to start even if model loading fails

### Error Handling

The API handles various error scenarios:
- Empty text input (400 Bad Request)
- Model initialization failure (500 Internal Server Error)
- Classification errors (500 Internal Server Error with details)

### Logging

All classification requests are logged with:
- Text length
- Classification result
- Confidence score
- Any errors encountered

## Dependencies

Required Python packages (already in `requirements.txt`):
```
transformers>=4.30.0
torch>=2.0.0
```

## Testing

Test the classification endpoint with various scenarios:

```python
# Test cases
test_texts = [
    "Ja, dit mag gepubliceerd worden.",  # Agrees
    "Nee, ik wil niet dat dit openbaar wordt.",  # Objects
    "Bedankt voor het bericht.",  # Neutral
    "Ik heb hier geen bezwaar tegen.",  # Agrees (double negative)
]

for text in test_texts:
    response = requests.post(
        "http://localhost:8000/classification/classify",
        json={"text": text}
    )
    result = response.json()
    print(f"\nText: {text}")
    print(f"Result: {result['classification']} ({result['confidence']:.2%})")
```

## Future Improvements

Potential enhancements:
1. **Fine-tuning**: Train on actual WOO responses for better accuracy
2. **Multi-class**: Add more nuanced categories (conditional agreement, unclear, etc.)
3. **Explanation**: Provide reasoning for classification decisions
4. **Batch Processing**: Support classifying multiple texts in one request
5. **Caching**: Cache results for identical texts
6. **Language Detection**: Auto-detect and optimize for input language

## Troubleshooting

### Model Fails to Load

If you see "Failed to initialize classification model" errors:

1. Ensure PyTorch is installed correctly:
   ```bash
   pip install torch transformers
   ```

2. Check available disk space (model downloads ~100MB)

3. Verify internet connectivity (first run downloads the model)

4. Check logs for detailed error messages

### Low Confidence Scores

If classifications consistently have low confidence:
- Review the input text for clarity
- Consider whether the text is truly about publication agreement
- Check if the text is in Dutch (optimal) or another language
- Ambiguous statements may need human review

### Performance Issues

If classification is slow:
- First request is slower (model loading)
- Subsequent requests should be fast (<1 second)
- Consider implementing caching for repeated texts
- For batch processing, consider grouping requests

