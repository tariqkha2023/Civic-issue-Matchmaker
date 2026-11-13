import {discover} from './discovery-search.js';
import {profileMatch} from './profile-match.js';

const el = id => document.getElementById(id);
function node(tag, text, parent, className) {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  parent.append(element);
  return element;
}
function link(text, url, parent) {
  const a = node('a', text, parent);
  if (/^https:\/\//.test(url)) a.href = url;
  a.target = '_blank'; a.rel = 'noopener noreferrer';
  return a;
}
function section(card, heading, text, className) {
  const box = className ? node('div', '', card, className) : card;
  node('h3', heading, box); node('p', text, box);
}
function card({issue: x, reason}, parent, profile) {
  const article = node('article', '', parent);
  article.id = `issue-${x.id}`;
  node('small', `${x.project[0]} · ${x.status} · ${x.assignment === 'unassigned' ? 'No assignee recorded' : x.assignment}`, article);
  node('h2', x.summary, article);
  node('p', `Original title: ${x.title}`, article, 'original-title');
  if (reason) node('p', reason, article, 'reason');
  const match = profileMatch(x, profile);
  const scoreBox = node('section', '', article, 'match-panel');
  scoreBox.setAttribute('aria-label', 'Personal match score');
  node('h3', 'Estimated match score · test profile', scoreBox);
  node('strong', match.score === null ? 'Insufficient information' : `${match.score}%`, scoreBox, 'match-value');
  node('p', match.explanation, scoreBox);
  node('small', 'Personal compatibility is separate from search relevance. Profile choices do not filter or reorder results.', scoreBox);
  section(article, 'What this project does', x.project[1], 'context');
  section(article, 'Background', x.background);
  section(article, 'Motivation', x.purpose);
  section(article, 'Work described', x.work);
  node('h3', 'Suggested skills', article);
  node('p', x.suggestedSkills.length ? 'These skills may help with the described work; they are not confirmed requirements.' : 'The posting is too broad to suggest a task-specific skill. Choose a concrete subtask first.', article);
  const list = node('ul', '', article, 'skill-list');
  x.suggestedSkills.forEach(s => node('li', s.name, list));
  if (x.suggestedSkills.length) {
    const details = node('details', '', article);
    node('summary', 'Why these skills are suggested', details);
    x.suggestedSkills.forEach(s => {
      node('h4', s.name, details); node('p', s.reason, details);
      node('blockquote', `From the original issue: “${s.quote}”`, details);
    });
  }
  section(article, 'Skills recorded in original metadata', x.recordedSkills.join(', ') || 'None recorded. This does not mean no skills are needed.');
  section(article, 'What still needs clarification', x.uncertainty, 'unknown');
  const details = node('details', '', article);
  node('summary', 'Original posting and sources', details);
  node('p', 'Explanations are interpretations of the saved posting and linked project documentation. Current issue state and implementation details should be checked on GitHub.', details);
  node('pre', x.description || 'No description supplied.', details);
  const sources = node('ul', '', details);
  [x.url, x.project[2], ...x.sources].forEach(url => link(url, url, node('li', '', sources)));
  link('View original issue on GitHub', x.url, node('p', '', article));
}

try {
  const [data, metadata, suggestions] = await Promise.all(
    ['context-review.json', 'sample-metadata.json', 'suggested-skills.json'].map(async name => {
      const response = await fetch(new URL(name, import.meta.url));
      if (!response.ok) throw new Error(`Could not load ${name}`);
      return response.json();
    }),
  );
  const issues = data.issues.map(x => ({...x, ...metadata.issues[x.id], suggestedSkills: suggestions[x.id] || []}));
  for (const [id, values] of [
    ['project', issues.map(x => x.project[0])],
    ['topic', issues.flatMap(x => x.topics)],
    ['skill', issues.flatMap(x => [...x.recordedSkills, ...x.suggestedSkills.map(s => s.name)])],
  ]) {
    [...new Set(values)].sort().forEach(value => {
      const option = node('option', value, el(id)); option.value = value;
    });
  }
  let page = 1;
  const pageSize = 5;
  for (const [id, values] of [
    ['profile-skills', ['Python','JavaScript','TypeScript','React','HTML','CSS','SQL','Documentation','Accessibility','Design','Testing','DevOps', ...issues.flatMap(x => [...x.recordedSkills, ...x.suggestedSkills.map(s => s.name)])]],
    ['profile-interests', issues.flatMap(x => x.topics)],
  ]) {
    [...new Set(values)].sort().forEach(value => {
      const label = node('label', '', el(id), 'check');
      const checkbox = node('input', '', label);
      checkbox.type = 'checkbox'; checkbox.value = value;
      node('span', value, label);
      checkbox.addEventListener('change', render);
    });
  }
  function selected(id) {
    return [...el(id).querySelectorAll('input:checked')].map(input => input.value);
  }
  function render() {
    const profile = {skills: selected('profile-skills'), interests: selected('profile-interests')};
    el('profile-status').textContent = `${profile.skills.length} skills and ${profile.interests.length} civic interests selected. Results are not filtered by this profile.`;
    const filters = Object.fromEntries(['q','project','topic','skill','status','assignment','sort'].map(id => [id, el(id).value]));
    filters.includeSuggested = el('suggested').checked;
    const found = discover(issues, filters);
    page = Math.min(page, Math.max(1, Math.ceil(found.length / pageSize)));
    el('results').replaceChildren();
    found.slice((page-1)*pageSize, page*pageSize).forEach(x => card(x, el('results'), profile));
    el('count').textContent = `${found.length} of 20 sample issues · Suggested skills ${filters.includeSuggested ? 'included' : 'excluded'} in search · Estimated scores use your test profile`;
    el('empty').hidden = found.length !== 0;
    el('page').textContent = `Page ${page} of ${Math.max(1, Math.ceil(found.length/pageSize))}`;
    el('previous').disabled = page === 1;
    el('next').disabled = page*pageSize >= found.length;
  }
  ['q','project','topic','skill','status','assignment','sort','suggested'].forEach(id => {
    el(id).addEventListener(id === 'q' ? 'input' : 'change', () => {page = 1; render();});
  });
  el('clear').onclick = () => {
    ['q','project','topic','skill','status','assignment'].forEach(id => {el(id).value = '';});
    el('sort').value = 'relevance'; el('suggested').checked = true; page = 1; render();
  };
  el('clear-profile').onclick = () => {
    document.querySelectorAll('.profile-panel input').forEach(input => {input.checked = false;});
    render();
  };
  for (const [id, step] of [['previous',-1],['next',1]]) {
    el(id).onclick = () => {page += step; render(); el('count').scrollIntoView({block:'start'});};
  }
  render();
} catch (error) {
  el('count').textContent = `The sample could not load. Refresh the page to retry. ${error.message}`;
  el('previous').disabled = true; el('next').disabled = true;
}
