jest.mock("react-native", () => ({
  Linking: {
    canOpenURL: jest.fn(),
    openURL: jest.fn(),
  },
}));

jest.mock("sonner-native", () => ({
  toast: {
    error: jest.fn(),
  },
}));

import {
  isHomeItemNavigable,
  navigateHomeItem,
} from "@/features/home/utils/home-item-navigation";

describe("home item navigation", () => {
  it("pushes policy document when documentId exists", async () => {
    const pushDocument = jest.fn();
    const canOpenUrl = jest.fn().mockResolvedValue(true);
    const openUrl = jest.fn().mockResolvedValue(undefined);
    const onCannotOpen = jest.fn();
    const onOpenFailed = jest.fn();

    await navigateHomeItem(
      {
        documentId: "  doc-123  ",
        sourceLink: "https://example.com/source",
        pushDocument,
      },
      {
        canOpenUrl,
        openUrl,
        onCannotOpen,
        onOpenFailed,
      },
    );

    expect(pushDocument).toHaveBeenCalledWith("doc-123");
    expect(canOpenUrl).not.toHaveBeenCalled();
    expect(openUrl).not.toHaveBeenCalled();
    expect(onCannotOpen).not.toHaveBeenCalled();
    expect(onOpenFailed).not.toHaveBeenCalled();
  });

  it("opens source link when documentId is missing", async () => {
    const pushDocument = jest.fn();
    const canOpenUrl = jest.fn().mockResolvedValue(true);
    const openUrl = jest.fn().mockResolvedValue(undefined);
    const onCannotOpen = jest.fn();
    const onOpenFailed = jest.fn();

    await navigateHomeItem(
      {
        documentId: " ",
        sourceLink: "  https://example.com/source-2  ",
        pushDocument,
      },
      {
        canOpenUrl,
        openUrl,
        onCannotOpen,
        onOpenFailed,
      },
    );

    expect(pushDocument).not.toHaveBeenCalled();
    expect(canOpenUrl).toHaveBeenCalledWith("https://example.com/source-2");
    expect(openUrl).toHaveBeenCalledWith("https://example.com/source-2");
    expect(onCannotOpen).not.toHaveBeenCalled();
    expect(onOpenFailed).not.toHaveBeenCalled();
  });

  it("does nothing when both documentId and sourceLink are missing", async () => {
    const pushDocument = jest.fn();
    const canOpenUrl = jest.fn().mockResolvedValue(true);
    const openUrl = jest.fn().mockResolvedValue(undefined);
    const onCannotOpen = jest.fn();
    const onOpenFailed = jest.fn();

    await navigateHomeItem(
      {
        documentId: null,
        sourceLink: " ",
        pushDocument,
      },
      {
        canOpenUrl,
        openUrl,
        onCannotOpen,
        onOpenFailed,
      },
    );

    expect(pushDocument).not.toHaveBeenCalled();
    expect(canOpenUrl).not.toHaveBeenCalled();
    expect(openUrl).not.toHaveBeenCalled();
    expect(onCannotOpen).not.toHaveBeenCalled();
    expect(onOpenFailed).not.toHaveBeenCalled();
    expect(isHomeItemNavigable({ documentId: null, sourceLink: " " })).toBe(
      false,
    );
  });
});
