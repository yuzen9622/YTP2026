const mockSecureSetItem = jest.fn();
const mockSecureGetItem = jest.fn();
const mockSecureDeleteItem = jest.fn();

jest.mock("expo-secure-store", () => ({
  __esModule: true,
  getItemAsync: (...args: unknown[]) => mockSecureGetItem(...args),
  setItemAsync: (...args: unknown[]) => mockSecureSetItem(...args),
  deleteItemAsync: (...args: unknown[]) => mockSecureDeleteItem(...args),
}));

import { useUserStore } from "../user-store";

describe("user-store", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useUserStore.setState({
      user: null,
      token: null,
    });
  });

  it("sets user with normalized name", () => {
    useUserStore.getState().setUser({
      id: "user-1",
      email: "tester@example.com",
      name: "Tester",
    });

    const state = useUserStore.getState();
    expect(state.user?.id).toBe("user-1");
    expect(state.user?.name).toBe("Tester");
  });

  it("persists token and clears token", async () => {
    mockSecureSetItem.mockResolvedValue(undefined);
    mockSecureDeleteItem.mockResolvedValue(undefined);

    await useUserStore.getState().setToken("token-123", "refresh-456");
    expect(useUserStore.getState().token).toBe("token-123");
    expect(mockSecureSetItem).toHaveBeenCalledWith("auth_token", "token-123");
    expect(mockSecureSetItem).toHaveBeenCalledWith(
      "refresh_token",
      "refresh-456",
    );

    await useUserStore.getState().setToken(null, null);
    expect(useUserStore.getState().token).toBeNull();
    expect(mockSecureDeleteItem).toHaveBeenCalledWith("auth_token");
    expect(mockSecureDeleteItem).toHaveBeenCalledWith("refresh_token");
  });

  it("clears in-memory session data", () => {
    useUserStore.setState({
      user: {
        id: "user-1",
        email: "tester@example.com",
        name: "Tester",
        profile: {
          userId: "user-1",
          age: 24,
          fieldTags: ["design"],
          location: "Taipei",
          expectedSalary: "30k_40k",
          careerStage: "job_seeking",
          educationLevel: "bachelor",
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      },
      token: "token-123",
    });

    useUserStore.getState().clearSession();

    const state = useUserStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(mockSecureDeleteItem).toHaveBeenCalledWith("auth_token");
    expect(mockSecureDeleteItem).toHaveBeenCalledWith("refresh_token");
  });
});
