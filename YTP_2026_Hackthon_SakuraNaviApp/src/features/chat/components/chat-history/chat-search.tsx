import { memo, useCallback, useEffect, useRef, useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";
import { CircleX, Search } from "lucide-react-native";
import { useChatSearchStore } from "@/features/chat/store/chat-search-store";
import { colors } from "@/lib/colors.ios";

export const ChatSearch = memo(function ChatSearch() {
  const [localQuery, setLocalQuery] = useState("");
  const [isInputVisible, setIsInputVisible] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<TextInput>(null);

  const { isActive, search, clearSearch } = useChatSearchStore();

  useEffect(() => {
    if (!isActive) {
      setLocalQuery("");
      setIsInputVisible(false);
    }
  }, [isActive]);

  const handleSearch = useCallback(
    (text: string) => {
      setLocalQuery(text);

      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      if (!text.trim()) {
        clearSearch();
        return;
      }

      debounceRef.current = setTimeout(() => {
        search(text);
      }, 400);
    },
    [search, clearSearch],
  );

  const handleOpenSearch = useCallback(() => {
    setIsInputVisible(true);
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  const handleCloseSearch = useCallback(() => {
    clearSearch();
    setIsInputVisible(false);
  }, [clearSearch]);

  const handleClearInput = useCallback(() => {
    setLocalQuery("");
    clearSearch();
    inputRef.current?.focus();
  }, [clearSearch]);

  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  if (!isInputVisible && !isActive) {
    return (
      <Pressable
        onPress={handleOpenSearch}
        className="h-10 w-10 items-center justify-center rounded-full bg-secondary"
      >
        <Search size={20} color={colors.foreground} />
      </Pressable>
    );
  }

  return (
    <View className="flex-row items-center flex-1 max-w-[200]">
      <View className="flex-row items-center flex-1 h-10 rounded-full bg-secondary px-3">
        <Search size={16} color={colors.mutedForeground} />
        <TextInput
          ref={inputRef}
          value={localQuery}
          onChangeText={handleSearch}
          placeholder="搜尋對話..."
          placeholderTextColor={colors.mutedForeground}
          className="flex-1 text-[15px] text-foreground ml-2"
          returnKeyType="search"
          autoCorrect={false}
          autoCapitalize="none"
        />
        {localQuery.length > 0 && (
          <Pressable onPress={handleClearInput} className="p-1">
            <CircleX size={16} color={colors.mutedForeground} />
          </Pressable>
        )}
      </View>

      {isActive && (
        <Pressable
          onPress={handleCloseSearch}
          className="h-10 items-center justify-center px-3"
        >
          <Text className="text-[15px] font-medium text-primary">取消</Text>
        </Pressable>
      )}
    </View>
  );
});
