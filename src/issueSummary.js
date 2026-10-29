// A source excerpt, never a generated description. The original remains available.
export function issueSummary(markdown = '', limit = 300) {
  const text = markdown
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/```[\s\S]*?(?:```|$)/g, '')
    .replace(/~~~[\s\S]*?(?:~~~|$)/g, '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/^\s*\[[^\]]+\]:.*$/gm, '')
    .replace(/<[^>]*>/g, '')
    .replace(/^\s{0,3}(?:#{1,6}\s+|>\s*|[-*+]\s+|\d+\.\s+|[-*_]{3,}\s*$)/gm, '')
    .replace(/\[[ xX]\]\s*/g, '')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/(\*\*|__|~~)(.+?)\1/g, '$2')
    .replace(/(^|\s)[*_]([^*_]+)[*_](?=\s|[.,!?]|$)/g, '$1$2')
    .replace(/\s+/g, ' ').trim();
  if (text.length <= limit) return text;
  const cut = text.slice(0, limit);
  const boundary = cut.lastIndexOf(' ');
  return cut.slice(0, boundary > limit / 2 ? boundary : limit).trimEnd() + '…';
}
