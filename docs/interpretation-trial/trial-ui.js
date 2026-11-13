import {discover} from './discovery-search.js';

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
function card({issue: x, reason}, parent) {
  const article = node('article', '', parent);
  article.id = `issue-${x.id}`;
  node('small', `${x.project[0]} · ${x.status} · ${x.assignment === 'unassigned' ? 'No assignee recorded' : x.assignment}`, article);
  node('h2', x.summary, article);
  node('p', `Original title: ${x.title}`, article, 'original-title');
  if (reason) node('p', reason, article, 'reason');
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
  function render() {
    const filters = Object.fromEntries(['q','project','topic','skill','status','assignment','sort'].map(id => [id, el(id).value]));
    filters.includeSuggested = el('suggested').checked;
    const found = discover(issues, filters);
    page = Math.min(page, Math.max(1, Math.ceil(found.length / pageSize)));
    el('results').replaceChildren();
    found.slice((page-1)*pageSize, page*pageSize).forEach(x => card(x, el('results')));
    el('count').textContent = `${found.length} of 20 sample issues · Suggested skills ${filters.includeSuggested ? 'included' : 'excluded'} · No personal score changes`;
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
  for (const [id, step] of [['previous',-1],['next',1]]) {
    el(id).onclick = () => {page += step; render(); el('count').scrollIntoView({block:'start'});};
  }
  render();
} catch (error) {
  el('count').textContent = `The sample could not load. Refresh the page to retry. ${error.message}`;
  el('previous').disabled = true; el('next').disabled = true;
}
