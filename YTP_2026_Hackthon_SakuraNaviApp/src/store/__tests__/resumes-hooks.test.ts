import { QueryClient } from "@tanstack/react-query";
import {
  invalidateResumes,
  RESUMES_QUERY_KEY,
} from "@/features/user-profile/hooks/resumes-query";

describe("resumes hooks", () => {
  it("invalidates resumes query key", async () => {
    const queryClient = new QueryClient();
    const spy = jest.spyOn(queryClient, "invalidateQueries").mockResolvedValue();

    await invalidateResumes(queryClient);

    expect(spy).toHaveBeenCalledWith({ queryKey: RESUMES_QUERY_KEY });
  });
});
