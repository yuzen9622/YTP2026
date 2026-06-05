export function parseSuggestions(content: string): {
  cleanContent: string;
  suggestions: string[];
  thinking?: string;
} {
  const suggestRegex = /\[SUGGEST:\s*(.+?)\]/g;
  const suggestions: string[] = [];
  let match: RegExpExecArray | null = null;

  while ((match = suggestRegex.exec(content)) !== null) {
    suggestions.push(match[1].trim());
  }

  const closedThinkRegex = /<think(?:ing)?>([\s\S]*?)<\/think(?:ing)?>/i;
  const closedMatch = closedThinkRegex.exec(content);

  let thinking: string | undefined;
  if (closedMatch) {
    thinking = closedMatch[1].trim() || undefined;
  } else {
    const openMatch = /<think(?:ing)?>/i.exec(content);
    if (openMatch) {
      const partial = content.slice(openMatch.index + openMatch[0].length).trim();
      thinking = partial || undefined;
    }
  }

  const cleanContent = content
    .replace(/\[SUGGEST:\s*.+?\]/g, "")
    .replace(/<think(?:ing)?>[\s\S]*?<\/think(?:ing)?>/gi, "")
    .replace(/<think(?:ing)?>[\s\S]*$/i, "")
    .trim();

  return {
    cleanContent,
    suggestions: suggestions.slice(0, 3),
    thinking,
  };
}
