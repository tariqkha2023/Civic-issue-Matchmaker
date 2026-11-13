// Preview-only estimated compatibility using recorded and researched inferred skills.
const names = values => [...new Set((values || []).map(x => x.trim().toLowerCase()).filter(Boolean))];

export function profileMatch(issue, profile) {
  const recorded = names(issue.recordedSkills);
  const inferred = names((issue.suggestedSkills || []).map(s => s.name)).filter(s => !recorded.includes(s));
  const required = [...recorded, ...inferred];
  const skills = names(profile.skills);
  const topics = names(issue.topics);
  const interests = names(profile.interests);
  if (!required.length || !skills.length) {
    return {
      score: null,
      explanation: !required.length
        ? 'This issue has neither recorded nor task-specific inferred skills. Civic interests alone cannot establish technical fit.'
        : 'Select your technical skills in the test profile to calculate a match.',
    };
  }
  const matched = required.filter(s => skills.includes(s));
  const skillFit = matched.length / required.length;
  const hasInterestFactor = topics.length > 0 && interests.length > 0;
  const interestFit = hasInterestFactor ? topics.filter(t => interests.includes(t)).length / topics.length : 0;
  return {
    score: Math.round(1000 * (hasInterestFactor ? 0.8 * skillFit + 0.2 * interestFit : skillFit)) / 10,
    inferred: inferred.length > 0,
    explanation: `${matched.length} of ${required.length} assessed skills match. ` +
      `Matched: ${matched.join(', ') || 'none'}. ` +
      `Not in your profile: ${required.filter(s => !skills.includes(s)).join(', ') || 'none'}. ` +
      (inferred.length ? `Inferred from the task: ${inferred.join(', ')}. These are suggestions, not confirmed requirements. ` : '') +
      (hasInterestFactor ? 'Skills contribute 80%; civic interests contribute 20%.' : 'Only skills are scored because civic interests or issue topics are missing.') +
      (hasInterestFactor ? ` Matching interests: ${topics.filter(t => interests.includes(t)).join(', ') || 'none'}.` : '') +
      ' Each distinct skill counts equally. This is an estimated compatibility comparison, not a probability of success.',
  };
}
