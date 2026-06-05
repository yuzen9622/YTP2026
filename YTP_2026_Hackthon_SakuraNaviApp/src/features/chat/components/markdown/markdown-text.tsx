import { Fragment, useMemo } from "react";
import { useColorScheme, View } from "react-native";
import { useMarkdown } from "react-native-marked";
import { ChatMarkdownRenderer } from "./chat-markdown-renderer";

interface MarkdownTextProps {
  content: string;
  isUser?: boolean;
}

export function MarkdownText({ content, isUser = false }: MarkdownTextProps) {
  const colorScheme = useColorScheme();

  const renderer = useMemo(() => new ChatMarkdownRenderer({ isUser }), [isUser]);

  const nodes = useMarkdown(content, {
    renderer,
    colorScheme,
    styles: {
      paragraph: { marginVertical: 0, paddingVertical: 0 },
      list: { marginVertical: 0 },
      h1: { marginVertical: 0 },
      h2: { marginVertical: 0 },
      h3: { marginVertical: 0 },
      h4: { marginVertical: 0 },
      h5: { marginVertical: 0 },
      h6: { marginVertical: 0 },
    },
  });

  return (
    <View style={{ flexShrink: 1, minWidth: 0, width: "100%" }}>
      {nodes.map((node, index) => (
        <Fragment key={index}>{node}</Fragment>
      ))}
    </View>
  );
}
