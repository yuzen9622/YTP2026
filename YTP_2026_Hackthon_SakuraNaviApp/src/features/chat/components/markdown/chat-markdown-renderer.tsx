import type { ReactNode } from "react";
import { Linking, View } from "react-native";
import { Renderer, type RendererInterface } from "react-native-marked";
import { Text } from "@/components/ui/text";
import { cn } from "@/lib/utils";

interface ChatRendererOptions {
  isUser?: boolean;
}

const BASE_TEXT = "text-[15px] leading-[22px]";
const WRAP_TEXT_STYLE = { flexShrink: 1, minWidth: 0 } as const;

export class ChatMarkdownRenderer
  extends Renderer
  implements RendererInterface
{
  private isUser: boolean;
  private fgClass: string;
  private mutedClass: string;
  private codeBgClass: string;
  private codeTextClass: string;
  private linkClass: string;
  private quoteBorderClass: string;

  constructor({ isUser = false }: ChatRendererOptions = {}) {
    super();
    this.isUser = isUser;
    this.fgClass = isUser ? "text-primary-foreground" : "text-foreground";
    this.mutedClass = isUser
      ? "text-primary-foreground/80"
      : "text-muted-foreground";
    this.codeBgClass = isUser ? "bg-primary-foreground/15" : "bg-background/60";
    this.codeTextClass = isUser ? "text-primary-foreground" : "text-foreground";
    this.linkClass = isUser
      ? "text-primary-foreground underline"
      : "text-primary underline";
    this.quoteBorderClass = isUser
      ? "border-primary-foreground/40"
      : "border-muted-foreground/40";
  }

  paragraph(children: ReactNode[]): ReactNode {
    return (
      <View key={this.getKey()} className="mb-1.5 min-w-0 w-full">
        <Text
          selectable
          className={cn(BASE_TEXT, this.fgClass)}
          style={WRAP_TEXT_STYLE}
        >
          {children}
        </Text>
      </View>
    );
  }

  text(children: string | ReactNode[]): ReactNode {
    if (typeof children === "string") {
      return (
        <Text
          key={this.getKey()}
          selectable
          className={cn(BASE_TEXT, this.fgClass)}
          style={WRAP_TEXT_STYLE}
        >
          {children}
        </Text>
      );
    }
    return (
      <Text
        key={this.getKey()}
        selectable
        className={cn(BASE_TEXT, this.fgClass)}
        style={WRAP_TEXT_STYLE}
      >
        {children}
      </Text>
    );
  }

  heading(children: string | ReactNode[], _styles?: unknown, depth?: number): ReactNode {
    const level = depth ?? 1;
    const sizeClass =
      level === 1
        ? "text-xl font-bold"
        : level === 2
          ? "text-lg font-bold"
          : level === 3
            ? "text-base font-semibold"
            : "text-sm font-semibold";
    return (
      <View key={this.getKey()} className="mt-1 mb-1.5">
        <Text selectable className={cn(sizeClass, this.fgClass)}>
          {children}
        </Text>
      </View>
    );
  }

  strong(children: string | ReactNode[]): ReactNode {
    return (
      <Text key={this.getKey()} className={cn("font-bold", this.fgClass)}>
        {children}
      </Text>
    );
  }

  em(children: string | ReactNode[]): ReactNode {
    return (
      <Text key={this.getKey()} className={cn("italic", this.fgClass)}>
        {children}
      </Text>
    );
  }

  del(children: string | ReactNode[]): ReactNode {
    return (
      <Text
        key={this.getKey()}
        className={cn("line-through", this.mutedClass)}
      >
        {children}
      </Text>
    );
  }

  codespan(text: string): ReactNode {
    return (
      <Text
        key={this.getKey()}
        className={cn(
          "rounded px-1 font-mono text-[13px]",
          this.codeBgClass,
          this.codeTextClass,
        )}
      >
        {text}
      </Text>
    );
  }

  code(text: string, language?: string): ReactNode {
    return (
      <View
        key={this.getKey()}
        className={cn(
          "my-1.5 self-stretch overflow-hidden rounded-lg border",
          this.isUser ? "border-primary-foreground/20" : "border-border",
          this.codeBgClass,
        )}
      >
        {language ? (
          <View
            className={cn(
              "border-b px-3 py-1",
              this.isUser
                ? "border-primary-foreground/15"
                : "border-border/60",
            )}
          >
            <Text className={cn("text-[11px] uppercase", this.mutedClass)}>
              {language}
            </Text>
          </View>
        ) : null}
        <View className="px-3 py-2">
          <Text
            selectable
            className={cn("font-mono text-[13px] leading-5", this.codeTextClass)}
          >
            {text}
          </Text>
        </View>
      </View>
    );
  }

  blockquote(children: ReactNode[]): ReactNode {
    return (
      <View
        key={this.getKey()}
        className={cn("my-1 border-l-2 pl-3", this.quoteBorderClass)}
      >
        {children}
      </View>
    );
  }

  hr(): ReactNode {
    return (
      <View
        key={this.getKey()}
        className={cn(
          "my-2 h-px",
          this.isUser ? "bg-primary-foreground/30" : "bg-border",
        )}
      />
    );
  }

  list(ordered: boolean, li: ReactNode[], _ls?: unknown, _ts?: unknown, startIndex = 1): ReactNode {
    return (
      <View key={this.getKey()} className="my-1 min-w-0 self-stretch gap-1">
        {li.map((item, index) => (
          <View
            key={`${this.getKey()}-li-${index}`}
            className="min-w-0 flex-row items-start gap-2"
          >
            <Text className={cn(BASE_TEXT, this.mutedClass, "min-w-[18px]")}>
              {ordered ? `${startIndex + index}.` : "•"}
            </Text>
            <View style={{ flex: 1, minWidth: 0, width: 0 }}>{item}</View>
          </View>
        ))}
      </View>
    );
  }

  listItem(children: ReactNode[]): ReactNode {
    const hasOnlyStrings = children.every((child) => typeof child === "string");

    return (
      <View key={this.getKey()} className="min-w-0 flex-1 basis-0 shrink">
        {hasOnlyStrings ? (
          <Text
            selectable
            className={cn(BASE_TEXT, this.fgClass)}
            style={WRAP_TEXT_STYLE}
          >
            {children}
          </Text>
        ) : (
          children
        )}
      </View>
    );
  }

  link(children: string | ReactNode[], href: string): ReactNode {
    return (
      <Text
        key={this.getKey()}
        accessibilityRole="link"
        className={this.linkClass}
        onPress={() => openLink(href)}
      >
        {children}
      </Text>
    );
  }

  br(): ReactNode {
    return (
      <Text key={this.getKey()} className={cn(BASE_TEXT, this.fgClass)}>
        {"\n"}
      </Text>
    );
  }

  escape(text: string): ReactNode {
    return this.text(text);
  }

  html(children: string | ReactNode[]): ReactNode {
    return this.text(children);
  }

  image(): ReactNode {
    return null;
  }

  linkImage(): ReactNode {
    return null;
  }

  table(header: ReactNode[][], rows: ReactNode[][][]): ReactNode {
    const borderClass = this.isUser
      ? "border-primary-foreground/25"
      : "border-border";
    const headerBgClass = this.isUser
      ? "bg-primary-foreground/10"
      : "bg-muted-foreground/10";
    const cellTextClass = cn("text-[13px] leading-5", this.fgClass);
    const headerTextClass = cn(
      "text-[13px] font-semibold leading-5",
      this.fgClass,
    );

    const renderCell = (
      cell: ReactNode[],
      colIndex: number,
      lastCol: boolean,
      isHeader: boolean,
    ) => (
      <View
        key={`c-${colIndex}`}
        className={cn(
          "flex-1 px-2 py-1.5 border-r",
          lastCol && "border-r-0",
          borderClass,
        )}
      >
        <Text selectable className={isHeader ? headerTextClass : cellTextClass}>
          {cell}
        </Text>
      </View>
    );

    return (
      <View
        key={this.getKey()}
        className={cn(
          "my-1.5 self-stretch overflow-hidden rounded-lg border",
          borderClass,
        )}
      >
        <View className={cn("flex-row", headerBgClass)}>
          {header.map((cell, idx) =>
            renderCell(cell, idx, idx === header.length - 1, true),
          )}
        </View>
        {rows.map((row, rowIdx) => (
          <View
            key={`r-${rowIdx}`}
            className={cn("flex-row border-t", borderClass)}
          >
            {row.map((cell, colIdx) =>
              renderCell(cell, colIdx, colIdx === row.length - 1, false),
            )}
          </View>
        ))}
      </View>
    );
  }
}

function openLink(href: string) {
  if (!/^https?:\/\//i.test(href) && !/^mailto:/i.test(href)) {
    return;
  }
  Linking.openURL(href).catch(() => {});
}
