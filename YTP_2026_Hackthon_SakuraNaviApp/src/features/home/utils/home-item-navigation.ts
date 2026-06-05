import { Linking } from "react-native";
import { toast } from "sonner-native";

export interface HomeItemNavigationTarget {
  documentId?: string | null;
  sourceLink?: string | null;
}

interface HomeItemNavigationParams extends HomeItemNavigationTarget {
  pushDocument: (documentId: string) => void;
}

interface HomeItemNavigationDeps {
  canOpenUrl: (url: string) => Promise<boolean>;
  openUrl: (url: string) => Promise<void>;
  onCannotOpen: () => void;
  onOpenFailed: () => void;
}

const defaultNavigationDeps: HomeItemNavigationDeps = {
  canOpenUrl: (url) => Linking.canOpenURL(url),
  openUrl: (url) => Linking.openURL(url),
  onCannotOpen: () => toast.error("無法開啟來源連結"),
  onOpenFailed: () => toast.error("開啟來源連結失敗"),
};

function normalizeText(value?: string | null): string | null {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

export function isHomeItemNavigable(target: HomeItemNavigationTarget): boolean {
  return (
    normalizeText(target.documentId) !== null ||
    normalizeText(target.sourceLink) !== null
  );
}

export async function navigateHomeItem(
  params: HomeItemNavigationParams,
  deps: HomeItemNavigationDeps = defaultNavigationDeps,
): Promise<void> {
  const documentId = normalizeText(params.documentId);
  if (documentId) {
    params.pushDocument(documentId);
    return;
  }

  const sourceLink = normalizeText(params.sourceLink);
  if (!sourceLink) {
    return;
  }

  try {
    const canOpen = await deps.canOpenUrl(sourceLink);
    if (!canOpen) {
      deps.onCannotOpen();
      return;
    }

    await deps.openUrl(sourceLink);
  } catch {
    deps.onOpenFailed();
  }
}
