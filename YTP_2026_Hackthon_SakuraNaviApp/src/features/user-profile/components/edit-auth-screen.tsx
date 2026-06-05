import { Stack, useRouter } from "expo-router";
import { ChevronLeft } from "lucide-react-native";
import React from "react";
import { Pressable, ScrollView, Text, TextInput, View } from "react-native";
import { colors } from "@/lib/colors.ios";
import { Label } from "@/components/ui/label";
import { Section } from "./section";
import useEditAuth from "../hooks/use-edit-auth";
import { Button } from "@/components/ui/button";

export function EditAuthScreen() {
  const router = useRouter();

  const {
    handleChangePasswordPayload,
    changePasswordPayload,
    handleChangePassword,
    isChangingPassword,
  } = useEditAuth();

  const handleBack = () => {
    router.back();
  };
  return (
    <>
      <Stack.Screen
        options={{
          title: "登入與密碼",
          headerLeft: () => (
            <Pressable
              onPress={handleBack}
              className="items-center justify-center rounded-full shadow-sm w-9 h-9 active:opacity-70"
            >
              <ChevronLeft
                size={20}
                className="text-foreground"
                color={colors.foreground}
              />
            </Pressable>
          ),
        }}
      />
      <ScrollView
        contentInsetAdjustmentBehavior="automatic"
        className="flex-1 p-4"
      >
        <Section title="修改密碼">
          <View className="px-4 py-3">
            <Label className="text-muted-foreground text-[13px] mb-1">
              目前密碼
            </Label>
            <TextInput
              value={changePasswordPayload.current_password}
              onChangeText={(v) =>
                handleChangePasswordPayload("current_password", v)
              }
              secureTextEntry={true}
              placeholder="輸入目前密碼"
              className="h-10 px-0 bg-transparent border-0 border-b border-border focus:border-primary focus:border-b-[2px] rounded-none text-[16px] text-foreground"
            />
          </View>
          <View className="px-4 py-3">
            <Label className="text-muted-foreground text-[13px] mb-1">
              新密碼
            </Label>
            <TextInput
              secureTextEntry={true}
              value={changePasswordPayload.new_password}
              onChangeText={(v) =>
                handleChangePasswordPayload("new_password", v)
              }
              placeholder="輸入新密碼"
              className="h-10 px-0 bg-transparent border-0 border-b border-border focus:border-primary focus:border-b-[2px] rounded-none text-[16px] text-foreground"
            />
          </View>
          <View className="px-4 py-3">
            <Button
              size="lg"
              className="w-full"
              onPress={handleChangePassword}
              disabled={isChangingPassword}
            >
              <Text className=" text-secondary">修改密碼</Text>
            </Button>
          </View>
        </Section>
      </ScrollView>
    </>
  );
}
