import { Platform } from "react-native";
import Head from "expo-router/head";
import { PRIVATE_ROBOTS } from "./indexability-policy";

export function NoIndexHead() {
  if (Platform.OS !== "web") {
    return null;
  }

  return (
    <Head>
      <meta name="robots" content={PRIVATE_ROBOTS} />
    </Head>
  );
}
