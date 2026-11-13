// Local pilot only. Suggestions broaden discovery; they never feed matching.py.
export const synonymGroups = [
  ['login', 'signin', 'authentication'],
  ['frontend', 'front end'],
  ['backend', 'back end'],
  ['javascript', 'js'],
  ['documentation', 'docs'],
  ['api', 'apis'],
  ['tile', 'tiles'], ['report', 'reports'], ['email', 'emails'],
  ['ingredient', 'ingredients'], ['map', 'maps', 'mapping'],
];

export function normalize(value = '') {
  return String(value).toLowerCase().replace(/sign[ -]in/g, 'signin')
    .replace(/front[ -]end/g, 'frontend').replace(/back[ -]end/g, 'backend')
    .replace(/[^\p{L}\p{N}+#.]+/gu, ' ').trim();
}

function contains(text, term) {
  return ` ${normalize(text)} `.includes(` ${term} `);
}

function matches(text, term, expand) {
  if (contains(text, term)) return true;
  if (!expand) return false;
  const group = synonymGroups.find(g => g.map(normalize).includes(term));
  return !!group?.some(other => contains(text, normalize(other)));
}

export function searchIssue(issue, query, includeSuggested = true) {
  const terms = [...new Set(normalize(query).split(/\s+/).filter(Boolean))];
  const task = [issue.title, issue.summary, issue.purpose, issue.work,
    ...(issue.recordedSkills || [])].join(' ');
  const original = issue.description || '';
  const suggestions = includeSuggested ? (issue.suggestedSkills || []).map(s => s.name).join(' ') : '';
  const background = [issue.background, issue.project[1], ...(issue.topics || [])].join(' ');
  const levels = [task, `${task} ${original}`, `${task} ${original} ${suggestions}`,
    `${task} ${original} ${suggestions} ${background}`];
  if (!terms.length) return {rank: 0, reason: ''};
  // Search only named fields: uncertainty, provenance and suggestion reasons are excluded.
  for (let rank = 0; rank < levels.length; rank++) {
    if (terms.every(term => matches(levels[rank], term, true))) {
      const expanded = !terms.every(term => matches(levels[rank], term, false));
      return {rank, reason: [
        'Found in task description', 'Found in original posting',
        'Suggested skill match', 'Related through project background',
      ][rank] + (expanded ? ' · related wording' : '')};
    }
  }
  return null;
}

export function discover(issues, filters = {}) {
  const {q = '', project = '', topic = '', skill = '', status = '', assignment = '',
    includeSuggested = true, sort = 'relevance'} = filters;
  return issues.flatMap((issue, index) => {
    if (project && issue.project[0] !== project) return [];
    if (topic && !issue.topics?.includes(topic)) return [];
    if (status && issue.status !== status) return [];
    if (assignment && issue.assignment !== assignment) return [];
    const recorded = (issue.recordedSkills || []).some(s => normalize(s) === normalize(skill));
    const suggested = includeSuggested && (issue.suggestedSkills || []).some(s => normalize(s.name) === normalize(skill));
    if (skill && !recorded && !suggested) return [];
    const match = searchIssue(issue, q, includeSuggested);
    if (!match) return [];
    const skillReason = skill && !recorded ? `Suggested skill match: ${skill}` : skill ? `Recorded skill match: ${skill}` : '';
    return [{issue, index, rank: match.rank, reason: [match.reason, skillReason].filter(Boolean).join(' · ')}];
  }).sort((a, b) => (sort === 'relevance' ? a.rank - b.rank : 0) || a.index - b.index);
}
