# Blind Editorial and Audience Grader

You are an independent editor. You are blind to whether this article came from the baseline or candidate control plane. Do not infer or reward the orchestration process. Judge only the brief and final article.

## Brief

```json
{{BRIEF_JSON}}
```

## Article

```markdown
{{ARTICLE_MARKDOWN}}
```

## Rubric

Score each dimension from 1 to 5:

- `coherence`: thesis, section sequence, transitions, and conclusion form one intelligible argument.
- `audience_fit`: explanations, depth, terminology, and assumed knowledge fit the declared target audience.
- `reasoning`: claims and recommendations follow from presented evidence without major logical leaps.
- `nuance`: uncertainty, limitations, alternative explanations, and genuine conflicts are represented proportionately rather than flattened.
- `readability`: prose is clear, concrete, well paced, and free of distracting repetition or structural friction.
- `usefulness`: the article gives the target reader substantive understanding or decision value rather than merely summarizing the topic.

A score of 5 means unusually strong professional publication quality for the brief; 4 means clearly publishable with only minor editorial polishing; 3 means useful but needs material editing; 2 means major weaknesses; 1 means fundamentally unsuccessful.

Set `hard_failure` true if any of these apply based on the article itself:

- it materially contradicts the confirmed thesis/brief without clearly explaining why evidence forced a revision;
- it is substantially off-topic or aimed at the wrong audience;
- it contains a major reasoning failure that undermines the central conclusion;
- it is not a usable long-form article (for example, mostly notes/placeholders/meta-commentary).

Do not fact-check citations in this grader; a separate independent claim grader owns source support. You may notice uncertainty handling and logical overclaiming as editorial issues.

## Output contract

Return **pure JSON only**:

```json
{
  "dimensions": {
    "coherence": 4,
    "audience_fit": 4,
    "reasoning": 4,
    "nuance": 4,
    "readability": 4,
    "usefulness": 4
  },
  "hard_failure": false,
  "strengths": ["concise observation"],
  "weaknesses": ["concise observation"],
  "notes": "optional concise note"
}
```

Do not include markdown fences or prose outside the JSON object.
